"""
PRD 生成服务
根据 DevSmart_PRD_v1.0.md Section 5.1.4 和 5.1.5 定义
生成双版本 PRD：Human PRD (Markdown) + Machine PRD (YAML)
支持模板选择
使用技能系统进行 PRD 生成
"""

from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import yaml
import os
from pathlib import Path

from models.conversation import Conversation
from models.document_version import DocumentVersion
from models.project import Project
from services.settings_service import SettingsService
from services.template_service import TemplateService
from utils.llm_client import LLMClient
from config.settings import settings

from skills.catalog import build_default_registry
from skills.runner import SkillRunner
from skills.models import SkillContext
from workflows import WorkflowEngine

_runner = SkillRunner(build_default_registry())
_workflow_engine = WorkflowEngine(_runner, workflows_dir="workflows")
_workflow_engine.load_workflows()


class PRDService:
    """PRD 生成服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.skill_runner = _runner
        self.workflow_engine = _workflow_engine

    async def generate_prd(
        self,
        project_id: str,
        conversation_id: Optional[str] = None,
        template_id: Optional[str] = None
    ) -> Dict:
        """
        生成双版本 PRD

        Args:
            project_id: 项目 ID
            conversation_id: 对话 ID（可选）
            template_id: 模板 ID（可选，默认使用通用SaaS模板）

        Returns:
            {
                "human_prd_path": "docs/human_prd_v1.md",
                "machine_prd_path": "docs/machine_prd_v1.yaml",
                "version": 1,
                "status": "success"
            }
        """
        # 1. 获取项目信息
        project = await self._get_project(project_id)
        if not project:
            raise ValueError(f"项目不存在: {project_id}")

        # 2. 获取对话历史
        conversations = await self._get_conversations(project_id)
        
        # 构建需求数据
        requirements = {}
        for conv in conversations:
            if conv.role == "user":
                requirements[str(conv.id)] = conv.content

        # 3. 使用工作流引擎生成 PRD
        context = SkillContext(project_id=project_id)
        
        try:
            workflow_result = await self.workflow_engine.execute(
                "devsmart.workflow.prd-generation",
                {
                    "project_name": project.name,
                    "requirements": requirements,
                    "human_prd": "",
                },
                context,
            )
            
            human_prd_content = workflow_result["steps"].get("generate_human_prd", {}).get("markdown", "")
            machine_prd_output = workflow_result["steps"].get("generate_machine_prd", {})
            
            if not human_prd_content:
                human_prd_content = await self._generate_human_prd(
                    conversations,
                    project.name,
                    project.description,
                    template_id
                )
            
            machine_prd_content = yaml.safe_dump(machine_prd_output, allow_unicode=True, sort_keys=False) if machine_prd_output else ""
            
            if not machine_prd_content:
                machine_prd_content = await self._generate_machine_prd(
                    conversations,
                    project.name,
                    project.description
                )
                
        except Exception as e:
            human_prd_content = await self._generate_human_prd(
                conversations,
                project.name,
                project.description,
                template_id
            )
            machine_prd_content = await self._generate_machine_prd(
                conversations,
                project.name,
                project.description
            )

        # 5. 确定版本号
        version = await self._get_next_version(project_id, "human_prd")

        # 6. 保存文档到数据库
        human_prd_doc = DocumentVersion(
            project_id=project_id,
            doc_type="human_prd",
            version=version,
            content=human_prd_content,
            change_summary="初始版本 - 通过对话生成",
            created_at=datetime.utcnow()
        )
        self.db.add(human_prd_doc)

        machine_prd_doc = DocumentVersion(
            project_id=project_id,
            doc_type="machine_prd",
            version=version,
            content=machine_prd_content,
            change_summary="初始版本 - 通过对话生成",
            created_at=datetime.utcnow()
        )
        self.db.add(machine_prd_doc)

        # 7. 保存到本地文件系统
        try:
            human_prd_path = await self._save_to_file(
                project_id,
                f"human_prd_v{version}.md",
                human_prd_content
            )
            machine_prd_path = await self._save_to_file(
                project_id,
                f"machine_prd_v{version}.yaml",
                machine_prd_content
            )
        except Exception as e:
            print(f"保存文件失败: {e}")
            raise

        # 8. 更新 project.json
        try:
            await self._update_project_json(project_id, version)
        except Exception as e:
            print(f"更新project.json失败: {e}")
            # 不影响主流程，继续执行

        await self.db.commit()

        return {
            "human_prd_path": human_prd_path,
            "machine_prd_path": machine_prd_path,
            "version": version,
            "status": "success"
        }

    async def _generate_human_prd(
        self,
        conversations: List[Conversation],
        project_name: str,
        project_description: Optional[str],
        template_id: Optional[str] = None
    ) -> str:
        """
        生成 Human PRD（Markdown 格式）

        Args:
            conversations: 对话历史列表
            project_name: 项目名称
            project_description: 项目描述
            template_id: 模板 ID（可选）

        Returns:
            Human PRD 内容（Markdown）
        """
        # 构建对话摘要文本
        conversation_text = ""
        for conv in conversations:
            if conv.role in ["user", "assistant"]:
                conversation_text += f"[{conv.role}]: {conv.content}\n\n"

        # 获取模板并构建提示词
        template_service = TemplateService()
        
        if template_id:
            template = template_service.get_template(template_id)
            if not template:
                template = template_service.get_default_template()
        else:
            template = template_service.get_default_template()

        # 使用模板构建提示词
        prompt = template_service.build_prompt_from_template(
            template,
            project_name,
            project_description or "",
            conversation_text
        )

        # 调用 LLM 生成 PRD
        settings_service = SettingsService(self.db)
        llm_config = await settings_service.get_effective_llm_config()
        client = LLMClient(llm_config)

        response = await client.chat([{"role": "user", "content": prompt}])
        content = response["content"]
        
        # 过滤掉 LLM 的思考过程块（包括内容）
        if '<think>' in content:
            end_tag = '</think>'
            end_idx = content.find(end_tag)
            if end_idx != -1:
                content = content[end_idx + len(end_tag):].strip()
        
        return content

    async def _generate_machine_prd(
        self,
        conversations: List[Conversation],
        project_name: str,
        project_description: Optional[str]
    ) -> str:
        """
        生成 Machine PRD（JSON 格式）

        Args:
            conversations: 对话历史列表
            project_name: 项目名称
            project_description: 项目描述

        Returns:
            Machine PRD 内容（JSON）
        """
        # 构建对话摘要文本
        conversation_text = ""
        for conv in conversations:
            if conv.role in ["user", "assistant"]:
                conversation_text += f"[{conv.role}]: {conv.content}\n\n"

        # 调用 LLM 生成 Machine PRD（JSON 格式）
        settings_service = SettingsService(self.db)
        llm_config = await settings_service.get_effective_llm_config()
        client = LLMClient(llm_config)

        # 构建 JSON 示例模板（避免在 .format() 中使用）
        json_template = """
{
  "project_name": "项目名称",
  "description": "一句话描述",
  "version": "1.0.0",
  "modules": [
    {
      "id": "module-001",
      "name": "模块名称",
      "features": ["功能1", "功能2"],
      "user_stories": [
        {"role": "用户角色", "action": "想要做什么", "benefit": "达到什么目标"}
      ]
    }
  ],
  "data_models": [
    {
      "id": "model-001",
      "name": "实体名称",
      "fields": [
        {"name": "字段名", "type": "string", "required": true, "description": "字段描述"}
      ],
      "relations": [
        {"target": "关联实体", "type": "one-to-many"}
      ]
    }
  ],
  "api_endpoints": [
    {
      "id": "api-001",
      "path": "/api/path",
      "method": "GET",
      "auth": true,
      "description": "接口描述",
      "request_body": {},
      "response_body": {},
      "error_codes": []
    }
  ],
  "non_functional": {
    "performance": {"concurrent_users": 100, "response_time": "200ms"},
    "security": {"auth_type": "JWT", "encryption": "AES256"},
    "scalability": {"strategy": "horizontal_scaling"}
  },
  "integrations": [
    {"id": "int-001", "name": "第三方服务名称", "type": "payment", "provider": "提供商"}
  ],
  "test_plan": {
    "unit_tests": [
      {
        "id": "unit-001",
        "feature_id": "feature-001",
        "test_name": "测试名称",
        "test_description": "测试描述",
        "test_file": "tests/unit/test_file.py"
      }
    ],
    "integration_tests": [
      {
        "id": "int-001",
        "feature_id": "feature-001",
        "test_name": "测试名称",
        "test_description": "测试描述",
        "test_file": "tests/integration/test_file.py"
      }
    ],
    "playwright_tests": [
      {
        "id": "e2e-001",
        "feature_id": "feature-001",
        "test_name": "测试名称",
        "test_description": "测试描述",
        "test_file": "tests/e2e/test_file.spec.ts",
        "test_scenarios": ["场景1", "场景2"]
      }
    ],
    "ci_loop": {
      "test_commands": {
        "unit": "pytest tests/unit/ -v --tb=short",
        "integration": "pytest tests/integration/ -v --tb=short",
        "e2e": "npx playwright test --reporter=line"
      },
      "result_format": {
        "type": "json",
        "parser": "pytest --json-report --json-report-file=test-results.json",
        "output_key": "results"
      },
      "max_retries": 3,
      "current_retry": 0,
      "failure_analysis_prompt": "分析以下测试失败信息，定位问题代码位置，提供具体的修复建议：\n{{failure_output}}",
      "fix_strategy": "根据失败分析结果，生成最小化代码补丁，只修改必要的代码行",
      "failure_handling": {
        "parse_failure": "提取测试名称、错误类型、错误消息、堆栈跟踪、涉及文件",
        "locate_code": "根据堆栈跟踪定位问题代码文件和行号",
        "generate_fix": "生成代码修复补丁",
        "apply_fix": "应用代码修复",
        "retry_test": "重新运行失败的测试"
      },
      "termination_conditions": [
        "all_tests_passed",
        "max_retries_reached",
        "same_failure_repeated_twice"
      ],
      "coverage_requirement": "代码覆盖率 >= 80%"
    }
  },
  "project_structure": {
    "backend": ["src/handlers/", "src/models/", "src/auth/", "src/error/", "src/db/", "main.rs"],
    "frontend": ["src/views/", "src/components/", "src/stores/", "src/api/", "src/router/", "src/types/"]
  },
  "error_format": {
    "structure": {"code": "业务错误码", "message": "用户友好提示", "request_id": "uuid"},
    "status_codes": {
      "400": "参数错误",
      "401": "未认证",
      "403": "无权限",
      "404": "资源不存在",
      "500": "服务器错误"
    }
  },
  "api_responses": [
    {
      "endpoint": "/api/path",
      "method": "GET",
      "response_body": {"data": [], "total": 0},
      "pagination": true
    }
  ],
  "database_schema": {
    "tables": [
      {
        "name": "table_name",
        "sql": "CREATE TABLE ..."
      }
    ],
    "indexes": [
      {
        "name": "idx_name",
        "table": "table_name",
        "columns": ["column1"],
        "type": "unique"
      }
    ]
  },
  "frontend_routes": [
    {
      "path": "/path",
      "view": "ComponentName",
      "description": "页面描述",
      "features": ["功能1", "功能2"]
    }
  ],
  "test_specifications": [
    {
      "module": "模块名称",
      "scenarios": [
        {
          "name": "场景名称",
          "description": "场景描述",
          "expected_result": "预期结果"
        }
      ]
    }
  ]
}
"""

        prompt = f"""请根据以下对话历史，生成一份 Machine PRD（JSON 格式），用于 LLM 自动生成代码。

项目名称：{project_name}
项目描述：{project_description or "无"}

对话历史：
{conversation_text}

请严格按照以下 JSON Schema 格式输出，注意：
1. JSON 中的布尔值使用 true/false（小写）
2. 所有 ID 字段必须是字符串类型，禁止使用 UUID 对象作为字典 key
3. 所有字段必须填写完整，不得遗漏

```json
{json_template}
```

请确保 JSON 格式正确，字段完整。只输出 JSON，不要包含其他内容。"""

        response = await client.chat([{"role": "user", "content": prompt}])

        # 提取 JSON 内容
        json_content = self._extract_json(response["content"])

        # 直接返回 JSON 格式的 Machine PRD（不再转换为 YAML，避免解析错误）
        return json_content

    def _extract_json(self, content: str) -> str:
        """从内容中提取 JSON"""
        # 尝试提取 ```json ... ``` 中的内容
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            if end > start:
                return content[start:end].strip()

        # 尝试提取 ``` ... ``` 中的内容
        if "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            if end > start:
                return content[start:end].strip()

        # 尝试直接解析整个内容
        if content.strip().startswith("{"):
            return content.strip()

        return "{}"

    async def _get_project(self, project_id: str) -> Optional[Project]:
        """获取项目信息"""
        query = select(Project).where(Project.id == project_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _get_conversations(self, project_id: str) -> List[Conversation]:
        """获取项目的对话历史"""
        query = select(Conversation).where(
            Conversation.project_id == project_id,
            Conversation.phase == "prd"
        ).order_by(Conversation.created_at.asc())
        result = await self.db.execute(query)
        return result.scalars().all()

    async def _get_next_version(self, project_id: str, doc_type: str) -> int:
        """获取下一个版本号"""
        query = select(DocumentVersion).where(
            DocumentVersion.project_id == project_id,
            DocumentVersion.doc_type == doc_type
        ).order_by(DocumentVersion.version.desc()).limit(1)
        result = await self.db.execute(query)
        last_version = result.scalar_one_or_none()

        if last_version:
            return last_version.version + 1
        return 1

    async def _save_to_file(
        self,
        project_id: str,
        filename: str,
        content: str
    ) -> str:
        """
        保存文档到本地文件系统

        Args:
            project_id: 项目 ID
            filename: 文件名
            content: 文件内容

        Returns:
            文件路径
        """
        # 获取项目信息
        project = await self._get_project(project_id)
        if not project:
            raise ValueError(f"项目不存在: {project_id}")

        # 创建项目目录
        project_dir = settings.projects_dir / project.name / "docs"
        project_dir.mkdir(parents=True, exist_ok=True)

        # 保存文件
        file_path = project_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        # 同时创建 current 版本（软链接或复制）
        current_filename = filename.replace(f"_v{await self._get_next_version(project_id, 'human_prd') - 1}", "_current")
        current_path = project_dir / current_filename
        with open(current_path, "w", encoding="utf-8") as f:
            f.write(content)

        return f"docs/{filename}"

    async def _update_project_json(self, project_id: str, version: int):
        """更新 project.json"""
        project = await self._get_project(project_id)
        if not project:
            return

        # 更新项目状态
        project.prd_version = version
        project.current_phase = "tech"  # 进入下一个阶段
        project.updated_at = datetime.utcnow()

        # 保存 project.json
        project_dir = settings.projects_dir / project.name
        project_json_path = project_dir / "project.json"

        project_data = {
            "id": str(project.id),
            "name": project.name,
            "description": project.description,
            "current_phase": project.current_phase,
            "prd_version": project.prd_version,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
            "docs": {
                "human_prd": f"docs/human_prd_v{version}.md",
                "machine_prd": f"docs/machine_prd_v{version}.json"
            }
        }

        import json
        with open(project_json_path, "w", encoding="utf-8") as f:
            json.dump(project_data, f, ensure_ascii=False, indent=2)

    async def get_prd(
        self,
        project_id: str,
        doc_type: str = "human_prd",
        version: Optional[int] = None
    ) -> Optional[DocumentVersion]:
        """获取指定版本的 PRD"""
        if version is None:
            # 获取最新版本
            query = select(DocumentVersion).where(
                DocumentVersion.project_id == project_id,
                DocumentVersion.doc_type == doc_type
            ).order_by(DocumentVersion.version.desc()).limit(1)
        else:
            query = select(DocumentVersion).where(
                DocumentVersion.project_id == project_id,
                DocumentVersion.doc_type == doc_type,
                DocumentVersion.version == version
            )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()