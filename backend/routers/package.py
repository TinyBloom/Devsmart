"""
Package Router
项目打包下载接口
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import get_db_session
from services.package_service import PackageService
from services.project_service import ProjectService

router = APIRouter(prefix="/api/projects", tags=["package"])


@router.get("/{project_id}/package")
async def download_package(
    project_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    下载项目打包文件

    Args:
        project_id: 项目 ID

    Returns:
        zip 文件流
    """
    try:
        # 验证项目存在
        project_service = ProjectService(db)
        project = await project_service.get_project_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目不存在: {project_id}"
            )

        # 生成打包文件
        package_service = PackageService(db)
        zip_content = await package_service.generate_package(project_id)

        # 返回文件流
        return StreamingResponse(
            iter([zip_content]),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={project.name}.zip",
                "Content-Type": "application/zip"
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"打包失败: {str(e)}"
        )


@router.get("/{project_id}/package/info")
async def get_package_info(
    project_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取打包信息

    Args:
        project_id: 项目 ID

    Returns:
        打包内容信息
    """
    try:
        project_service = ProjectService(db)
        project = await project_service.get_project_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目不存在: {project_id}"
            )

        package_service = PackageService(db)
        info = await package_service.get_package_info(project_id)

        return info
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
