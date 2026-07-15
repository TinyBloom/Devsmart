"""
Project Router
项目管理 API 路由
根据 DevSmart_PRD_v1.0.md Section 5.0.6 定义
"""

from typing import Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from models.database import get_db_session
from models.project import ProjectType
from services.project_service import ProjectService
from services.conversation_service import ConversationService


router = APIRouter(prefix="/api/projects", tags=["Projects"])


# Pydantic 模型定义
class ProjectCreateRequest(BaseModel):
    """创建项目请求"""
    name: str = Field(..., min_length=3, max_length=64, pattern=r'^[a-zA-Z0-9_-]+$')
    description: Optional[str] = None
    project_type: Optional[str] = ProjectType.GREENFIELD
    source_path: Optional[str] = None
    onboarding_data: Optional[Dict] = None


class ProjectUpdateRequest(BaseModel):
    """更新项目请求"""
    description: Optional[str] = None
    current_phase: Optional[str] = None
    prd_version: Optional[int] = None
    project_type: Optional[str] = None
    source_path: Optional[str] = None
    onboarding_data: Optional[Dict] = None


class ProjectResponse(BaseModel):
    """项目响应"""
    id: str
    name: str
    description: Optional[str]
    current_phase: str
    prd_version: int
    project_type: str
    source_path: Optional[str]
    created_at: str
    updated_at: str


class ProjectContextResponse(BaseModel):
    """项目上下文响应"""
    project: ProjectResponse
    project_json: dict
    docs_dir: str


@router.post("", response_model=ProjectResponse)
async def create_project(
    request: ProjectCreateRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """创建新项目"""
    service = ProjectService(db)
    try:
        project = await service.create_project(
            request.name, 
            request.description,
            request.project_type,
            request.source_path,
            request.onboarding_data
        )
        return ProjectResponse(**project.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/onboarding/template")
async def get_onboarding_template(
    db: AsyncSession = Depends(get_db_session)
):
    """获取 onboarding 模板配置"""
    service = ProjectService(db)
    template = await service.get_onboarding_template()
    return template


@router.get("", response_model=list[ProjectResponse])
async def get_projects(
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: AsyncSession = Depends(get_db_session)
):
    """获取项目列表"""
    service = ProjectService(db)
    projects = await service.get_project_list(search)
    return [ProjectResponse(**p.to_dict()) for p in projects]


@router.get("/{project_identifier}", response_model=ProjectResponse)
async def get_project(
    project_identifier: str,
    db: AsyncSession = Depends(get_db_session)
):
    """获取项目详情（支持按名称或 ID 查询）"""
    from services.project_service import ProjectService
    
    # 先尝试按 ID 查询
    service = ProjectService(db)
    project = await service.get_project_by_id(project_identifier)
    
    # 如果按 ID 查询不到，尝试按名称查询
    if not project:
        project = await service.get_project_by_name(project_identifier)
    
    if not project:
        raise HTTPException(status_code=404, detail=f"项目 '{project_identifier}' 不存在")
    
    return ProjectResponse(**project.to_dict())


@router.put("/{name}", response_model=ProjectResponse)
async def update_project(
    name: str,
    request: ProjectUpdateRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """更新项目信息"""
    service = ProjectService(db)

    update_data = request.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="没有提供更新数据")

    project = await service.update_project(name, **update_data)
    if not project:
        raise HTTPException(status_code=404, detail=f"项目 '{name}' 不存在")
    return ProjectResponse(**project.to_dict())


@router.delete("/{name}")
async def delete_project(
    name: str,
    db: AsyncSession = Depends(get_db_session)
):
    """删除项目"""
    service = ProjectService(db)
    success = await service.delete_project(name)
    if not success:
        raise HTTPException(status_code=404, detail=f"项目 '{name}' 不存在")
    return {"status": "success", "message": f"项目 '{name}' 已删除"}


@router.get("/{name}/context", response_model=ProjectContextResponse)
async def restore_project_context(
    name: str,
    db: AsyncSession = Depends(get_db_session)
):
    """恢复项目上下文"""
    service = ProjectService(db)
    try:
        context = await service.restore_project_context(name)
        return ProjectContextResponse(
            project=ProjectResponse(**context["project"]),
            project_json=context["project_json"],
            docs_dir=context["docs_dir"]
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{name}/conversations")
async def get_project_conversations(
    name: str,
    phase: Optional[str] = Query(None, description="筛选阶段"),
    limit: Optional[int] = Query(None, description="限制数量"),
    db: AsyncSession = Depends(get_db_session)
):
    """获取项目对话历史"""
    project_service = ProjectService(db)
    conversation_service = ConversationService(db)

    project = await project_service.get_project_by_name(name)
    if not project:
        raise HTTPException(status_code=404, detail=f"项目 '{name}' 不存在")

    conversations = await conversation_service.get_conversations_by_project(
        str(project.id), phase, limit
    )
    return {
        "project": name,
        "conversations": [c.to_dict() for c in conversations],
        "total": len(conversations)
    }


@router.get("/{project_identifier}/prd")
async def get_project_prd(
    project_identifier: str,
    doc_type: str = "human_prd",
    db: AsyncSession = Depends(get_db_session)
):
    """获取项目的 PRD 内容"""
    from services.prd_service import PRDService

    prd_service = PRDService(db)
    prd = await prd_service.get_prd(project_identifier, doc_type)

    if not prd:
        raise HTTPException(status_code=404, detail="PRD 不存在")

    return {
        "id": str(prd.id),
        "project_id": str(prd.project_id),
        "doc_type": prd.doc_type,
        "version": prd.version,
        "content": prd.content,
        "change_summary": prd.change_summary,
        "created_at": prd.created_at.isoformat()
    }


class DeltaPrdRequest(BaseModel):
    """增量 PRD 生成请求"""
    conversation_history: list[Dict] = Field(..., description="对话历史记录")
    previous_prd_path: Optional[str] = None


@router.post("/{name}/scan")
async def scan_project(
    name: str,
    db: AsyncSession = Depends(get_db_session)
):
    """扫描现有项目结构"""
    service = ProjectService(db)
    result = await service.scan_project(name)
    
    if result.get("status") == "ERROR":
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.post("/{name}/delta-prd")
async def generate_delta_prd(
    name: str,
    request: DeltaPrdRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """生成增量 PRD"""
    service = ProjectService(db)
    result = await service.generate_delta_prd(
        name,
        request.conversation_history,
        request.previous_prd_path
    )
    
    if result.get("status") == "ERROR":
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.get("/{name}/prd-history")
async def get_prd_history(
    name: str,
    db: AsyncSession = Depends(get_db_session)
):
    """获取项目 PRD 历史版本"""
    service = ProjectService(db)
    project = await service.get_project_by_name(name)
    
    if not project:
        raise HTTPException(status_code=404, detail=f"项目 '{name}' 不存在")
    
    history = await service.get_project_prd_history(name)
    
    return {
        "project": name,
        "versions": history,
        "total": len(history)
    }