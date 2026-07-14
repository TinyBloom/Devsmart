"""
Conversation Summary Model (Long-term Memory)
根据 DevSmart_PRD_v1.0.md Section 5.1.7 定义
"""

from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from datetime import datetime
import uuid

from models.database import Base, GUID


class ConversationSummary(Base):
    """对话摘要表（长期记忆）"""
    __tablename__ = "conversation_summaries"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    project_id = Column(GUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    phase = Column(String(20), nullable=False)
    summary = Column(Text, nullable=False)
    covers_up_to_id = Column(GUID, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "phase": self.phase,
            "summary": self.summary,
            "covers_up_to_id": str(self.covers_up_to_id),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }