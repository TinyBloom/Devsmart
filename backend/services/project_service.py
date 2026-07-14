"""
Project Service
项目管理服务，实现 DevSmart_PRD_v1.0.md Section 5.0 定义的功能
"""

import os
import json
import uuid
import aiofiles
from pathlib import Path
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from models.project import Project
from config.settings import settings


class ProjectService:
    """项目管理服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.projects_dir = settings.projects_dir

    async def create_project(self, name: str, description: Optional[str] = None) -> Project:
        """
        创建新项目
        根据 PRD Section 5.0.4 规则：
        - 项目名称必须唯一
        - 项目名称只能包含字母、数字、下划线、连字符
        - 项目名称长度 3-64 个字符
        - 创建项目时自动生成 project.json 初始状态文件
        """
        # 校验项目名称
        if not self._validate_project_name(name):
            raise ValueError(f"项目名称 '{name}' 不符合规则：只能包含字母、数字、下划线、连字符，长度 3-64")

        # 创建数据库记录
        project = Project(name=name, description=description)
        self.db.add(project)
        try:
            await self.db.commit()
            await self.db.refresh(project)
        except IntegrityError:
            await self.db.rollback()
            raise ValueError(f"项目名称 '{name}' 已存在")

        # 创建项目目录和 project.json
        await self._create_project_files(project)

        return project

    def _validate_project_name(self, name: str) -> bool:
        """校验项目名称是否符合规则"""
        if len(name) < 3 or len(name) > 64:
            return False
        import re
        return bool(re.match(r'^[a-zA-Z0-9_-]+$', name))

    async def _create_project_files(self, project: Project):
        """创建项目目录和 project.json"""
        project_dir = self.projects_dir / project.name
        project_dir.mkdir(parents=True, exist_ok=True)

        # 创建 docs 目录
        docs_dir = project_dir / "docs"
        docs_dir.mkdir(exist_ok=True)

        # 创建 project.json
        project_json = {
            "project_id": str(project.id),
            "project_name": project.name,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "current_phase": project.current_phase,
            "phases": {
                "prd": {"status": "pending"},
                "tech": {"status": "pending"},
                "prototype": {"status": "pending"},
                "scaffold": {"status": "pending"},
                "code": {"status": "pending"},
                "test": {"status": "pending"},
                "deploy": {"status": "pending"}
            },
            "modules": {},
            "artifacts": {},
            "settings": {
                "max_autofix_retries": settings.max_autofix_retries,
                "llm_provider": settings.llm_provider,
                "llm_model": settings.llm_model
            }
        }

        async with aiofiles.open(project_dir / "project.json", 'w', encoding='utf-8') as f:
            await f.write(json.dumps(project_json, indent=2, ensure_ascii=False))

    async def get_project_list(self, search: Optional[str] = None) -> List[Project]:
        """获取项目列表（支持搜索）"""
        query = select(Project).order_by(Project.updated_at.desc())
        if search:
            query = query.where(Project.name.ilike(f"%{search}%"))
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_project_by_name(self, name: str) -> Optional[Project]:
        """根据名称获取项目"""
        query = select(Project).where(Project.name == name)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_project_by_id(self, project_id: str) -> Optional[Project]:
        """根据 ID 获取项目"""
        try:
            # 验证 UUID 格式
            uuid_obj = uuid.UUID(project_id)
            
            # 使用 cast 来确保类型兼容
            from sqlalchemy import cast, String
            query = select(Project).where(cast(Project.id, String) == project_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except ValueError:
            return None

    async def update_project(self, name: str, **kwargs) -> Optional[Project]:
        """更新项目信息"""
        project = await self.get_project_by_name(name)
        if not project:
            return None

        # 更新数据库
        stmt = update(Project).where(Project.name == name).values(**kwargs)
        await self.db.execute(stmt)
        await self.db.commit()
        await self.db.refresh(project)

        # 更新 project.json
        await self._update_project_json(project)

        return project

    async def _update_project_json(self, project: Project):
        """更新 project.json"""
        project_dir = self.projects_dir / project.name
        project_json_path = project_dir / "project.json"

        if not project_json_path.exists():
            await self._create_project_files(project)
            return

        # 读取现有 project.json
        async with aiofiles.open(project_json_path, 'r', encoding='utf-8') as f:
            content = await f.read()
            project_json = json.loads(content)

        # 更新字段
        project_json["current_phase"] = project.current_phase
        project_json["updated_at"] = project.updated_at.isoformat() if project.updated_at else None

        # 写回文件
        async with aiofiles.open(project_json_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(project_json, indent=2, ensure_ascii=False))

    async def delete_project(self, name: str) -> bool:
        """删除项目（含所有关联数据和文件）"""
        project = await self.get_project_by_name(name)
        if not project:
            return False

        # 删除数据库记录（级联删除关联数据）
        await self.db.delete(project)
        await self.db.commit()

        # 删除项目目录
        project_dir = self.projects_dir / name
        if project_dir.exists():
            import shutil
            shutil.rmtree(project_dir)

        return True

    async def restore_project_context(self, name: str) -> dict:
        """
        恢复项目上下文
        根据 PRD Section 5.0.5 规则：
        1. 读取 project.json 获取当前阶段和状态
        2. 读取对话历史（最近 N 轮 + 摘要）
        3. 读取最新版本的 PRD
        4. 恢复到上次中断的界面继续工作
        """
        project = await self.get_project_by_name(name)
        if not project:
            raise ValueError(f"项目 '{name}' 不存在")

        project_dir = self.projects_dir / name
        project_json_path = project_dir / "project.json"

        # 读取 project.json
        if project_json_path.exists():
            async with aiofiles.open(project_json_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                project_json = json.loads(content)
        else:
            await self._create_project_files(project)
            project_json = {
                "project_id": str(project.id),
                "project_name": project.name,
                "current_phase": project.current_phase,
                "phases": {}
            }

        return {
            "project": project.to_dict(),
            "project_json": project_json,
            "docs_dir": str(project_dir / "docs"),
        }