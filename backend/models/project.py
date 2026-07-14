"""
Project Model
根据 DevSmart_PRD_v1.0.md Section 5.1.7 定义
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, JSON
from datetime import datetime
import uuid

from models.database import Base, GUID


class Project(Base):
    """项目表"""
    __tablename__ = "projects"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(64), unique=True, nullable=False, index=True)
    description = Column(Text)
    current_phase = Column(String(20), nullable=False, default="prd")
    prd_version = Column(Integer, nullable=False, default=0)
    # 技术栈配置（Phase 2）
    tech_stack = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "current_phase": self.current_phase,
            "prd_version": self.prd_version,
            "tech_stack": self.tech_stack,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }