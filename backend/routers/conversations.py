"""
对话管理 API 路由
根据 DevSmart_PRD_v1.0.md Section 5.1.6 定义
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from models.database import get_db_session
from models.conversation import Conversation
from services.conversation_service import ConversationService


router = APIRouter(prefix="/api/conversations", tags=["Conversations"])


class SendMessageRequest(BaseModel):
    """发送消息请求"""
    content: str
    phase: str = "prd"
    template_id: Optional[str] = None


class MessageResponse(BaseModel):
    """消息响应"""
    id: str
    project_id: str
    phase: str
    role: str
    content: str
    token_count: int
    completeness_score: Optional[float]
    created_at: str


class SendMessageResponse(BaseModel):
    """发送消息响应"""
    user_message: MessageResponse
    assistant_message: MessageResponse
    completeness_score: float
    is_ready_for_prd: bool


@router.post("/{project_id}/messages", response_model=SendMessageResponse)
async def send_message(
    project_id: str,
    request: SendMessageRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    用户发送消息，触发 LLM 回复

    Args:
        project_id: 项目 ID
        request: 发送消息请求

    Returns:
        发送消息响应（包含用户消息、助手消息、完整度分数）
    """
    service = ConversationService(db)

    try:
        result = await service.send_message(
            project_id=project_id,
            content=request.content,
            phase=request.phase,
            template_id=request.template_id
        )

        return SendMessageResponse(
            user_message=MessageResponse(
                id=str(result["user_message"].id),
                project_id=str(result["user_message"].project_id),
                phase=result["user_message"].phase,
                role=result["user_message"].role,
                content=result["user_message"].content,
                token_count=result["user_message"].token_count,
                completeness_score=result["user_message"].completeness_score,
                created_at=result["user_message"].created_at.isoformat()
            ),
            assistant_message=MessageResponse(
                id=str(result["assistant_message"].id),
                project_id=str(result["assistant_message"].project_id),
                phase=result["assistant_message"].phase,
                role=result["assistant_message"].role,
                content=result["assistant_message"].content,
                token_count=result["assistant_message"].token_count,
                completeness_score=result["assistant_message"].completeness_score,
                created_at=result["assistant_message"].created_at.isoformat()
            ),
            completeness_score=result["completeness_score"],
            is_ready_for_prd=result["is_ready_for_prd"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发送消息失败: {str(e)}")


@router.get("/{project_id}", response_model=List[MessageResponse])
async def get_conversations(
    project_id: str,
    phase: str = "prd",
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取项目的对话历史

    Args:
        project_id: 项目 ID
        phase: 阶段

    Returns:
        对话历史列表
    """
    service = ConversationService(db)
    conversations = await service.get_conversations(project_id, phase)

    return [
        MessageResponse(
            id=str(conv.id),
            project_id=str(conv.project_id),
            phase=conv.phase,
            role=conv.role,
            content=conv.content,
            token_count=conv.token_count,
            completeness_score=conv.completeness_score,
            created_at=conv.created_at.isoformat()
        )
        for conv in conversations
    ]