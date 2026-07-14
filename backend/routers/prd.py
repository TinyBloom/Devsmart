"""
PRD 生成 API 路由
根据 DevSmart_PRD_v1.0.md Section 5.1.6 定义
支持模板选择
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List

from models.database import get_db_session
from services.prd_service import PRDService
from services.template_service import TemplateService


router = APIRouter(prefix="/api/prd", tags=["PRD"])


class GeneratePRDRequest(BaseModel):
    """生成 PRD 请求"""
    project_id: str
    conversation_id: Optional[str] = None
    template_id: Optional[str] = None


class TemplateResponse(BaseModel):
    """模板响应"""
    id: str
    name: str
    description: str
    icon: str
    dimensions: dict


class GeneratePRDResponse(BaseModel):
    """生成 PRD 响应"""
    status: str
    human_prd_path: str
    machine_prd_path: str
    version: int
    project_id: str


class PRDContentResponse(BaseModel):
    """PRD 内容响应"""
    id: str
    project_id: str
    doc_type: str
    version: int
    content: str
    change_summary: Optional[str]
    created_at: str


@router.post("/generate", response_model=GeneratePRDResponse)
async def generate_prd(
    request: GeneratePRDRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    基于对话历史生成双版本 PRD

    Args:
        request: 生成 PRD 请求（支持模板选择）

    Returns:
        生成 PRD 响应
    """
    service = PRDService(db)

    try:
        result = await service.generate_prd(
            project_id=request.project_id,
            conversation_id=request.conversation_id,
            template_id=request.template_id
        )

        return GeneratePRDResponse(
            status=result["status"],
            human_prd_path=result["human_prd_path"],
            machine_prd_path=result["machine_prd_path"],
            version=result["version"],
            project_id=request.project_id
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成 PRD 失败: {str(e)}")


@router.get("/templates", response_model=List[TemplateResponse])
async def get_prd_templates():
    """
    获取所有可用的 PRD 模板列表

    Returns:
        模板列表
    """
    template_service = TemplateService()
    templates = template_service.get_templates()
    return templates


@router.get("/{project_id}", response_model=PRDContentResponse)
async def get_prd(
    project_id: str,
    doc_type: str = "human_prd",
    version: Optional[int] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取已生成的 PRD

    Args:
        project_id: 项目 ID
        doc_type: 文档类型（human_prd / machine_prd）
        version: 版本号（可选，默认获取最新版本）

    Returns:
        PRD 内容响应
    """
    service = PRDService(db)
    prd = await service.get_prd(project_id, doc_type, version)

    if not prd:
        raise HTTPException(status_code=404, detail="PRD 不存在")

    return PRDContentResponse(
        id=str(prd.id),
        project_id=str(prd.project_id),
        doc_type=prd.doc_type,
        version=prd.version,
        content=prd.content,
        change_summary=prd.change_summary,
        created_at=prd.created_at.isoformat()
    )


@router.get("/{project_id}/versions")
async def get_prd_versions(
    project_id: str,
    doc_type: str = "human_prd",
    db: AsyncSession = Depends(get_db_session)
):
    """获取 PRD 的所有版本列表"""
    from sqlalchemy import select
    from models.document_version import DocumentVersion

    query = select(DocumentVersion).where(
        DocumentVersion.project_id == project_id,
        DocumentVersion.doc_type == doc_type
    ).order_by(DocumentVersion.version.desc())

    result = await db.execute(query)
    versions = result.scalars().all()

    return {
        "project_id": project_id,
        "doc_type": doc_type,
        "versions": [
            {
                "version": v.version,
                "created_at": v.created_at.isoformat(),
                "change_summary": v.change_summary
            }
            for v in versions
        ]
    }