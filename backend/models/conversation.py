"""
Conversation Model
根据 DevSmart_PRD_v1.0.md Section 5.1.7 定义
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, Float, ForeignKey, CheckConstraint
from datetime import datetime
import uuid

from models.database import Base, GUID


class Conversation(Base):
    """对话历史表"""
    __tablename__ = "conversations"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    project_id = Column(GUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    phase = Column(String(20), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=False, default=0)
    completeness_score = Column(Float)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant', 'system')", name="check_role"),
    )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "phase": self.phase,
            "role": self.role,
            "content": self.content,
            "token_count": self.token_count,
            "completeness_score": self.completeness_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }