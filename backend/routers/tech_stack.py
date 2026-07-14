"""
技术栈路由
Phase 2: 技术选型 API
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import get_db_session
from services.tech_stack_service import TechStackRecommender, TechStackValidator
from services.project_service import ProjectService


router = APIRouter(prefix="/api/tech-stack", tags=["技术栈"])


class TechStackRequest(BaseModel):
    """技术栈请求"""
    project_name: str
    prd_data: Optional[dict] = None  # 如果不提供则使用项目的 PRD


class TechStackSelection(BaseModel):
    """用户选择的技术栈"""
    backend: dict
    frontend: Optional[dict] = None
    database: dict
    cache: Optional[dict] = None
    deployment: dict
    cicd: dict


class TechStackValidateRequest(BaseModel):
    """技术栈验证请求"""
    project_name: str
    selected_stack: TechStackSelection


@router.get("/library")
async def get_tech_stack_library():
    """获取完整的技术栈选项库（含权衡说明）"""
    from services.tech_stack_service import TECH_STACK_LIBRARY
    return {
        "status": "success",
        "library": TECH_STACK_LIBRARY
    }


@router.post("/recommend")
async def recommend_tech_stack(
    request: TechStackRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    推荐技术栈方案

    根据 PRD 内容分析需求特征，推荐 1-3 套技术方案
    """
    service = ProjectService(db)

    # 获取项目信息
    project = await service.get_project_by_name(request.project_name)
    if not project:
        raise HTTPException(status_code=404, detail=f"项目 '{request.project_name}' 不存在")

    # 使用提供的 PRD 数据或从项目加载
    prd_data = request.prd_data
    if not prd_data:
        # TODO: 从项目文档中加载 PRD 数据
        prd_data = {
            "features": [],
            "non_functional": {},
            "integrations": []
        }

    # 生成推荐
    recommender = TechStackRecommender(prd_data)
    recommendations = recommender.recommend()
    analysis = recommender.analyze_requirements()

    return {
        "status": "success",
        "analysis": analysis,
        "recommendations": recommendations
    }


@router.post("/validate")
async def validate_tech_stack(
    request: TechStackValidateRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    验证技术栈选择的合理性

    检查是否有冲突或潜在问题
    """
    service = ProjectService(db)

    # 获取项目信息
    project = await service.get_project_by_name(request.project_name)
    if not project:
        raise HTTPException(status_code=404, detail=f"项目 '{request.project_name}' 不存在")

    # TODO: 从项目文档中加载 PRD 数据
    prd_data = {
        "features": [],
        "non_functional": {},
        "integrations": []
    }

    # 验证选择
    validator = TechStackValidator(request.selected_stack.model_dump(), prd_data)
    result = validator.validate()

    return {
        "status": "success",
        "validation": result
    }


@router.get("/{project_name}")
async def get_project_tech_stack(
    project_name: str,
    db: AsyncSession = Depends(get_db_session)
):
    """获取项目的技术栈选择"""
    service = ProjectService(db)
    project = await service.get_project_by_name(project_name)

    if not project:
        raise HTTPException(status_code=404, detail=f"项目 '{project_name}' 不存在")

    if not project.tech_stack:
        return {
            "status": "success",
            "tech_stack": None,
            "message": "该项目尚未选择技术栈"
        }

    return {
        "status": "success",
        "tech_stack": project.tech_stack
    }


@router.put("/{project_name}")
async def update_project_tech_stack(
    project_name: str,
    tech_stack: TechStackSelection,
    db: AsyncSession = Depends(get_db_session)
):
    """
    保存项目的技术栈选择

    用户确认技术栈方案后调用此接口
    """
    service = ProjectService(db)
    project = await service.get_project_by_name(project_name)

    if not project:
        raise HTTPException(status_code=404, detail=f"项目 '{project_name}' 不存在")

    # 验证选择
    prd_data = {
        "features": [],
        "non_functional": {},
        "integrations": []
    }
    validator = TechStackValidator(tech_stack.model_dump(), prd_data)
    validation_result = validator.validate()

    # 保存技术栈
    success = await service.update_project(
        project_name,
        tech_stack=tech_stack.model_dump(),
        current_phase="prototype"  # Phase 2 完成，进入 Phase 3
    )

    if not success:
        raise HTTPException(status_code=500, detail="更新技术栈失败")

    return {
        "status": "success",
        "validation": validation_result,
        "message": "技术栈已保存"
    }
