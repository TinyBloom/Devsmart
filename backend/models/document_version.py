"""
Document Version Model
根据 DevSmart_PRD_v1.0.md Section 5.1.7 定义
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, CheckConstraint, UniqueConstraint
from datetime import datetime
import uuid

from models.database import Base, GUID


class DocumentVersion(Base):
    """文档版本表"""
    __tablename__ = "document_versions"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    project_id = Column(GUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    doc_type = Column(String(20), nullable=False)
    version = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    change_summary = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "doc_type IN ('human_prd', 'machine_prd', 'pages_spec', 'openapi', 'schema')",
            name="check_doc_type"
        ),
        UniqueConstraint("project_id", "doc_type", "version", name="unique_project_doc_version"),
    )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "doc_type": self.doc_type,
            "version": self.version,
            "content": self.content,
            "change_summary": self.change_summary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }