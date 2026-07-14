"""
DevSmart Routers Package
"""

from routers.project import router as project_router
from routers.settings import router as settings_router

__all__ = [
    "project_router",
    "settings_router",
]