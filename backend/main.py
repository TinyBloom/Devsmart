"""
DevSmart FastAPI Main Entry
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config.settings import settings
from models.database import init_database
from routers.project import router as project_router
from routers.settings import router as settings_router
from routers.conversations import router as conversation_router
from routers.prd import router as prd_router
from routers.tech_stack import router as tech_stack_router
from routers.package import router as package_router
from routers.skills import router as skills_router
from routers.workflows import router as workflows_router


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    await init_database()
    yield
    # 关闭时清理资源


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="DevSmart - LLM驱动的软件开发平台",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:5176", "http://localhost:5177", "http://localhost:5178"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(project_router)
app.include_router(settings_router)
app.include_router(conversation_router)
app.include_router(prd_router)
app.include_router(tech_stack_router)
app.include_router(package_router)
app.include_router(skills_router)
app.include_router(workflows_router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )