"""
Package Service
项目打包服务，将项目产物打包成 Agent 友好的目录结构
包含: prd/、tech_stack/、skills/、INSTRUCTIONS.md
"""

import os
import zipfile
import io
import shutil
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.project import Project
from models.document_version import DocumentVersion
from config.settings import settings


class PackageService:
    """项目打包服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.projects_dir = settings.projects_dir
        self.skills_dir = settings.base_dir / "skills"
        
        self.template_env = Environment(
            loader=FileSystemLoader(settings.base_dir / "templates"),
            autoescape=False
        )

    async def generate_package(self, project_id: str) -> bytes:
        """
        生成项目打包文件（zip 格式）

        Args:
            project_id: 项目 ID

        Returns:
            zip 文件的二进制内容
        """
        # 获取项目信息
        project = await self._get_project(project_id)
        if not project:
            raise ValueError(f"项目不存在: {project_id}")

        project_dir = self.projects_dir / project.name
        docs_dir = project_dir / "docs"

        # 创建临时目录用于打包
        with io.BytesIO() as buffer:
            with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 1. 添加 PRD 文件
                await self._add_prd_files(zipf, project_id, docs_dir)

                # 2. 添加技术栈文件
                await self._add_tech_stack_files(zipf, project_id, docs_dir)

                # 3. 添加 Skill 文件
                self._add_skill_files(zipf)

                # 4. 生成并添加 INSTRUCTIONS.md
                instructions_content = await self._generate_instructions(project_id)
                zipf.writestr(f"{project.name}/INSTRUCTIONS.md", instructions_content)

            buffer.seek(0)
            return buffer.read()

    async def _get_project(self, project_id: str) -> Optional[Project]:
        """获取项目信息"""
        from sqlalchemy import cast, String
        query = select(Project).where(cast(Project.id, String) == project_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _get_prd_content(self, project_id: str, doc_type: str) -> Optional[str]:
        """获取 PRD 文档内容"""
        query = select(DocumentVersion).where(
            DocumentVersion.project_id == project_id,
            DocumentVersion.doc_type == doc_type
        ).order_by(DocumentVersion.version.desc()).limit(1)
        result = await self.db.execute(query)
        doc = result.scalar_one_or_none()
        return doc.content if doc else None

    async def _get_tech_stack(self, project_id: str) -> Optional[Dict]:
        """获取项目的技术栈配置"""
        project = await self._get_project(project_id)
        if not project or not project.tech_stack:
            return None
        return project.tech_stack

    async def _add_prd_files(self, zipf: zipfile.ZipFile, project_id: str, docs_dir: Path):
        """添加 PRD 文件到 zip"""
        project = await self._get_project(project_id)
        if not project:
            return

        # 从数据库读取最新版本的 PRD
        human_prd_content = await self._get_prd_content(project_id, "human_prd")
        machine_prd_content = await self._get_prd_content(project_id, "machine_prd")

        if human_prd_content:
            zipf.writestr(f"{project.name}/prd/human_prd.md", human_prd_content)

        if machine_prd_content:
            zipf.writestr(f"{project.name}/prd/machine_prd.json", machine_prd_content)

        # 如果数据库中没有，尝试从文件系统读取
        if not human_prd_content and (docs_dir / "human_prd_current.md").exists():
            with open(docs_dir / "human_prd_current.md", 'r', encoding='utf-8') as f:
                zipf.writestr(f"{project.name}/prd/human_prd.md", f.read())

        if not machine_prd_content and (docs_dir / "machine_prd_current.json").exists():
            with open(docs_dir / "machine_prd_current.json", 'r', encoding='utf-8') as f:
                zipf.writestr(f"{project.name}/prd/machine_prd.json", f.read())

    async def _add_tech_stack_files(self, zipf: zipfile.ZipFile, project_id: str, docs_dir: Path):
        """添加技术栈文件到 zip"""
        project = await self._get_project(project_id)
        if not project:
            return

        # 添加用户选择的技术栈
        tech_stack = await self._get_tech_stack(project_id)
        if tech_stack:
            tech_stack_yaml = yaml.dump(tech_stack, allow_unicode=True, default_flow_style=False)
            zipf.writestr(f"{project.name}/tech_stack/chosen_stack.yaml", tech_stack_yaml)

        # 尝试添加推荐的技术方案
        tech_options_path = docs_dir / "tech_options.yaml"
        if tech_options_path.exists():
            with open(tech_options_path, 'r', encoding='utf-8') as f:
                zipf.writestr(f"{project.name}/tech_stack/tech_options.yaml", f.read())

    def _add_skill_files(self, zipf: zipfile.ZipFile):
        """添加 Skill 文件到 zip"""
        if not self.skills_dir.exists():
            return

        for skill_type in ["prd", "tech"]:
            skill_type_dir = self.skills_dir / skill_type
            if not skill_type_dir.exists():
                continue

            for skill_name in os.listdir(skill_type_dir):
                skill_dir = skill_type_dir / skill_name
                if not skill_dir.is_dir():
                    continue

                for file_name in os.listdir(skill_dir):
                    file_path = skill_dir / file_name
                    
                    # 排除 __pycache__ 目录和 .pyc 文件
                    if file_name == "__pycache__":
                        continue
                    if file_name.endswith(".pyc"):
                        continue
                    
                    if file_path.is_file():
                        arcname = f"skills/{skill_type}/{skill_name}/{file_name}"
                        with open(file_path, 'rb') as f:
                            zipf.writestr(arcname, f.read())

    async def _generate_instructions(self, project_id: str) -> str:
        """生成 INSTRUCTIONS.md 内容"""
        project = await self._get_project(project_id)
        if not project:
            return ""

        # 获取 PRD 版本
        query = select(DocumentVersion).where(
            DocumentVersion.project_id == project_id,
            DocumentVersion.doc_type == "human_prd"
        ).order_by(DocumentVersion.version.desc()).limit(1)
        result = await self.db.execute(query)
        prd_doc = result.scalar_one_or_none()
        prd_version = prd_doc.version if prd_doc else 1

        # 获取技术栈
        tech_stack = await self._get_tech_stack(project_id)

        template = self.template_env.get_template("instructions.md.jinja2")
        return template.render(
            project_name=project.name,
            project_description=project.description or "无",
            prd_version=prd_version,
            tech_stack=tech_stack or {}
        )

    async def get_package_info(self, project_id: str) -> Dict[str, Any]:
        """
        获取打包信息（用于前端显示）

        Returns:
            包含打包内容信息的字典
        """
        project = await self._get_project(project_id)
        if not project:
            return {}

        human_prd = await self._get_prd_content(project_id, "human_prd")
        machine_prd = await self._get_prd_content(project_id, "machine_prd")
        tech_stack = await self._get_tech_stack(project_id)

        return {
            "project_name": project.name,
            "has_human_prd": bool(human_prd),
            "has_machine_prd": bool(machine_prd),
            "has_tech_stack": bool(tech_stack),
            "prd_version": project.prd_version or 1
        }
