"""
skill_prd_generate - Runner

根据对话历史生成双版本 PRD
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class PRDGenerateRunner:
    """PRD 生成 Skill Runner"""

    def __init__(self, project_dir: str, llm_service=None):
        """
        初始化 Runner

        Args:
            project_dir: 项目目录路径
            llm_service: LLM 服务实例
        """
        self.project_dir = Path(project_dir)
        self.llm_service = llm_service
        self.skill_dir = Path(__file__).parent

    async def run(
        self,
        conversation_history: List[Dict[str, Any]],
        project_name: str
    ) -> Dict[str, Any]:
        """
        执行 Skill

        Args:
            conversation_history: 对话历史
            project_name: 项目名称

        Returns:
            执行结果
        """
        try:
            # 1. 分析对话历史，提取需求
            requirements = self._extract_requirements(conversation_history)

            # 2. 检查需求完整度
            completeness = self._calculate_completeness(requirements)

            # 3. 如果完整度不足，返回错误
            if completeness["total_score"] < 80:
                return {
                    "status": "ERROR",
                    "message": "需求完整度不足 ({}/100)，请继续补充信息".format(completeness["total_score"]),
                    "completeness": completeness,
                    "missing_dimensions": completeness["missing"]
                }

            # 4. 生成 Human PRD
            human_prd = self._generate_human_prd(project_name, requirements)

            # 5. 生成 Machine PRD
            machine_prd = self._generate_machine_prd(project_name, requirements)

            # 6. 确定版本号
            version = self._get_next_version()

            # 7. 保存文件
            human_path = self.project_dir / "docs" / "human_prd_v{}.md".format(version)
            machine_path = self.project_dir / "docs" / "machine_prd_v{}.yaml".format(version)
            current_human = self.project_dir / "docs" / "human_prd_current.md"
            current_machine = self.project_dir / "docs" / "machine_prd_current.yaml"

            # 确保目录存在
            human_path.parent.mkdir(parents=True, exist_ok=True)

            # 写入文件
            with open(human_path, 'w', encoding='utf-8') as f:
                f.write(human_prd)

            with open(machine_path, 'w', encoding='utf-8') as f:
                yaml.dump(machine_prd, f, allow_unicode=True, default_flow_style=False)

            # 更新 current 文件
            with open(current_human, 'w', encoding='utf-8') as f:
                f.write(human_prd)

            with open(current_machine, 'w', encoding='utf-8') as f:
                yaml.dump(machine_prd, f, allow_unicode=True, default_flow_style=False)

            logger.info("PRD 已生成: human={}, machine={}".format(human_path, machine_path))

            return {
                "status": "SUCCESS",
                "message": "PRD 生成成功 (版本 {})".format(version),
                "version": version,
                "completeness": completeness,
                "artifacts": [
                    {"file_path": str(human_path), "type": "human_prd"},
                    {"file_path": str(machine_path), "type": "machine_prd"}
                ]
            }

        except Exception as e:
            logger.error("skill_prd_generate 执行失败: {}".format(e))
            return {
                "status": "ERROR",
                "message": "执行失败: {}".format(str(e))
            }

    def _extract_requirements(self, conversation_history: List[Dict]) -> Dict[str, Any]:
        """从对话历史中提取需求"""
        requirements = {
            "one_liner": "",
            "target_users": [],
            "core_value": "",
            "features": [],
            "data_models": [],
            "api_endpoints": [],
            "non_functional": {},
            "integrations": []
        }

        # 合并所有对话内容
        all_content = []
        for msg in conversation_history:
            if msg.get("role") == "user":
                all_content.append("用户: {}".format(msg.get('content', '')))
            elif msg.get("role") == "assistant":
                all_content.append("助手: {}".format(msg.get('content', '')))

        combined_text = "\n".join(all_content).lower()

        # 简单的关键词提取（实际应该用 LLM）
        # 目标用户关键词
        user_keywords = ["用户", "客户", "管理员", "admin", "user", "customer", "角色", "使用者"]
        for keyword in user_keywords:
            if keyword in combined_text:
                requirements["target_users"].append(keyword)

        # 功能关键词
        feature_keywords = ["功能", "模块", "feature", "管理", "查询", "展示"]
        for keyword in feature_keywords:
            if keyword in combined_text:
                if keyword not in requirements["features"]:
                    requirements["features"].append({
                        "name": "基于{}的功能".format(keyword),
                        "description": "从对话中提取的功能需求",
                        "user_stories": [],
                        "priority": "medium"
                    })

        # 数据模型关键词
        model_keywords = ["数据", "存储", "用户信息", "订单", "商品", "data", "model"]
        for keyword in model_keywords:
            if keyword in combined_text:
                if keyword not in [m["name"] for m in requirements["data_models"]]:
                    requirements["data_models"].append({
                        "name": keyword,
                        "fields": []
                    })

        # 非功能需求
        perf_keywords = ["性能", "并发", "响应时间", "performance"]
        if any(k in combined_text for k in perf_keywords):
            requirements["non_functional"]["performance"] = {
                "expected_users": "medium",
                "response_time": "normal"
            }

        # 集成需求
        integrate_keywords = ["集成", "对接", "第三方", "支付", "短信", "integration"]
        for keyword in integrate_keywords:
            if keyword in combined_text:
                if keyword not in [i["name"] for i in requirements["integrations"]]:
                    requirements["integrations"].append({
                        "name": keyword,
                        "purpose": "从对话中提取的集成需求",
                        "api_type": "REST"
                    })

        return requirements

    def _calculate_completeness(self, requirements: Dict) -> Dict[str, Any]:
        """计算需求完整度"""
        weights = {
            "core_features": 0.30,
            "user_roles": 0.15,
            "data_entities": 0.25,
            "non_functional": 0.15,
            "integrations": 0.15
        }

        scores = {}
        missing = []

        # 核心功能 (30%)
        if len(requirements.get("features", [])) >= 1:
            scores["core_features"] = 100
        else:
            scores["core_features"] = 0
            missing.append("core_features")

        # 用户角色 (15%)
        if len(requirements.get("target_users", [])) >= 1:
            scores["user_roles"] = 100
        else:
            scores["user_roles"] = 0
            missing.append("user_roles")

        # 数据实体 (25%)
        if len(requirements.get("data_models", [])) >= 1:
            scores["data_entities"] = 100
        else:
            scores["data_entities"] = 0
            missing.append("data_entities")

        # 非功能需求 (15%)
        if requirements.get("non_functional"):
            scores["non_functional"] = 100
        else:
            scores["non_functional"] = 50  # 部分满足
            missing.append("non_functional")

        # 外部集成 (15%)
        if len(requirements.get("integrations", [])) >= 1:
            scores["integrations"] = 100
        else:
            scores["integrations"] = 50  # 部分满足
            missing.append("integrations")

        # 计算总分
        total_score = sum(scores[k] * weights[k] for k in weights)

        return {
            "total_score": round(total_score, 1),
            "dimensions": scores,
            "missing": missing
        }

    def _generate_human_prd(self, project_name: str, requirements: Dict) -> str:
        """生成 Human PRD"""
        # 功能模块
        features_md = ""
        for i, feature in enumerate(requirements.get("features", []), 1):
            features_md += "### 2.{} {}\n".format(i, feature.get('name', 'TBD'))
            features_md += "- {}\n".format(feature.get('description', 'TBD'))
            for story in feature.get("user_stories", []):
                features_md += "  - As a {} I want {} so that {}\n".format(
                    story.get('as_a'), story.get('i_want'), story.get('so_that'))

        # 数据模型
        models_md = ""
        for i, model in enumerate(requirements.get("data_models", []), 1):
            models_md += "### 3.{} {}\n\n".format(i, model.get('name', 'TBD'))
            models_md += "| 字段 | 类型 | 必填 | 说明 |\n"
            models_md += "|---|---|---|---|\n"
            for field in model.get("fields", []):
                models_md += "| {} | {} | {} | {} |\n".format(
                    field.get('name', 'TBD'),
                    field.get('type', 'TBD'),
                    '是' if field.get('required') else '否',
                    field.get('description', '')
                )
            models_md += "\n"

        # API 接口
        api_md = "| 接口 | 方法 | 路径 | 说明 |\n"
        api_md += "|---|---|---|---|\n"
        for endpoint in requirements.get("api_endpoints", []):
            api_md += "| {} | {} | {} | - |\n".format(
                endpoint.get('description', 'TBD'),
                endpoint.get('method', 'TBD'),
                endpoint.get('path', 'TBD')
            )

        # 非功能需求
        nf = requirements.get("non_functional", {})
        nf_md = ""
        if nf.get("performance"):
            nf_md += "- **性能要求**：" + str(nf['performance']) + "\n"
        if nf.get("security"):
            nf_md += "- **安全要求**：" + str(nf['security']) + "\n"
        if nf.get("scalability"):
            nf_md += "- **扩展性要求**：" + str(nf['scalability']) + "\n"

        # 外部集成
        int_md = ""
        for integ in requirements.get("integrations", []):
            int_md += "- **{}**：{}\n".format(
                integ.get('name', 'TBD'),
                integ.get('purpose', 'TBD')
            )

        # 组装 PRD
        features_section = features_md if features_md else "_功能模块待补充_"
        models_section = models_md if models_md else "_数据模型待补充_"
        api_section = api_md if api_md else "_API 接口待补充_"
        nf_section = nf_md if nf_md else "_非功能需求待补充_"
        int_section = int_md if int_md else "_外部集成待补充_"

        target_users = ', '.join(requirements.get('target_users', ['TBD'])) or 'TBD'

        prd = """# {project_name}

## 1. 产品概述
- **一句话描述**：{one_liner}
- **目标用户**：{target_users}
- **核心价值**：{core_value}

## 2. 功能模块
{features}

## 3. 数据模型
{models}

## 4. API 接口清单
{api}

## 5. 非功能需求
{nf}

## 6. 外部集成
{integrations}
""".format(
            project_name=project_name,
            one_liner=requirements.get('one_liner', 'TBD'),
            target_users=target_users,
            core_value=requirements.get('core_value', 'TBD'),
            features=features_section,
            models=models_section,
            api=api_section,
            nf=nf_section,
            integrations=int_section
        )

        return prd

    def _generate_machine_prd(self, project_name: str, requirements: Dict) -> Dict:
        """生成 Machine PRD"""
        return {
            "project_name": project_name,
            "version": "1.0",
            "generated_at": self._get_timestamp(),
            "features": requirements.get("features", []),
            "data_models": requirements.get("data_models", []),
            "api_endpoints": requirements.get("api_endpoints", []),
            "non_functional": requirements.get("non_functional", {}),
            "integrations": requirements.get("integrations", [])
        }

    def _get_next_version(self) -> int:
        """获取下一个版本号"""
        docs_dir = self.project_dir / "docs"
        if not docs_dir.exists():
            return 1

        existing_versions = []
        for f in docs_dir.glob("human_prd_v*.md"):
            try:
                version_str = f.stem.replace("human_prd_v", "")
                existing_versions.append(int(version_str))
            except ValueError:
                continue

        return max(existing_versions, default=0) + 1

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        return datetime.utcnow().isoformat() + "Z"


# 作为独立脚本运行时
if __name__ == "__main__":
    import asyncio
    import sys
    import json

    async def main():
        if len(sys.argv) < 3:
            print("用法: python runner.py <project_name> <conversation_history_json>")
            sys.exit(1)

        project_name = sys.argv[1]
        history = json.loads(sys.argv[2])

        runner = PRDGenerateRunner(".")
        result = await runner.run(history, project_name)
        print(yaml.dump(result, allow_unicode=True))

    asyncio.run(main())
