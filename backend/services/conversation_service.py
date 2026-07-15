"""
对话管理服务
实现 Phase 1 对话流程，包含三层记忆策略（基于 RAG）
根据 DevSmart_PRD_v1.0.md Section 5.1.11 定义
使用技能系统进行需求分析和追问生成
"""

from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import json

from models.conversation import Conversation
from models.conversation_summary import ConversationSummary
from models.project import Project
from services.settings_service import SettingsService
from services.questioning_strategy import QuestioningStrategy
from services.completeness_calculator import CompletenessCalculator
from services.rag_service import RAGService
from utils.llm_client import LLMClient
from config.settings import settings

from skills.catalog import build_default_registry
from skills.runner import SkillRunner
from skills.models import SkillContext

_runner = SkillRunner(build_default_registry())


class ConversationService:
    """对话管理服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.questioning_strategy = QuestioningStrategy()
        self.skill_runner = _runner

    async def create_conversation(
        self,
        project_id: str,
        phase: str = "prd"
    ) -> Conversation:
        """
        创建新对话

        Args:
            project_id: 项目 ID
            phase: 阶段（prd/tech/prototype等）

        Returns:
            Conversation 对象
        """
        # 添加系统提示消息
        system_message = Conversation(
            project_id=project_id,
            phase=phase,
            role="system",
            content="你是一个专业的软件需求分析助手。你的任务是帮助用户梳理软件需求，通过追问逐步补全需求细节，最终生成一份完整的 PRD 文档。",
            token_count=50,
            created_at=datetime.utcnow()
        )
        self.db.add(system_message)
        await self.db.commit()
        await self.db.refresh(system_message)

        return system_message

    async def send_message(
        self,
        project_id: str,
        content: str,
        phase: str = "prd",
        template_id: Optional[str] = None
    ) -> Dict:
        """
        用户发送消息，触发 LLM 回复

        Args:
            project_id: 项目 ID
            content: 用户消息内容
            phase: 阶段
            template_id: 模板 ID（用于获取维度权重）

        Returns:
            {
                "user_message": Conversation,
                "assistant_message": Conversation,
                "completeness_score": float,
                "is_ready_for_prd": bool
            }
        """
        # 1. 保存用户消息
        user_message = Conversation(
            project_id=project_id,
            phase=phase,
            role="user",
            content=content,
            token_count=self._estimate_tokens(content),
            created_at=datetime.utcnow()
        )
        self.db.add(user_message)
        await self.db.commit()

        # 2. 获取项目信息
        project = await self._get_project(project_id)

        # 3. 获取 RAG 上下文（复用一次检索结果）
        rag_context = await self._get_rag_context(project_id, content, project)

        # 4. 获取对话历史（三层记忆策略）
        conversation_history = await self._get_conversation_context(project_id, phase, content, project)

        # 5. 生成 LLM 回复
        full_context = rag_context + conversation_history
        assistant_response = await self._generate_llm_response(
            full_context,
            content,
            project.name if project else "未命名项目"
        )

        # 6. 使用技能系统分析需求缺口和完整度
        all_conversations = rag_context + conversation_history + [{"role": "user", "content": content}]
        
        try:
            context = SkillContext(project_id=project_id)
            
            analyze_result = await self.skill_runner.run(
                "devsmart.requirement.analyze-gaps",
                {
                    "idea": content,
                    "conversation": all_conversations,
                    "requirements": {},
                },
                context,
            )
            
            completeness_result = {
                "total_score": analyze_result.output.get("completeness", 0),
                "is_complete": analyze_result.output.get("completeness", 0) >= 75,
                "dimensions": analyze_result.output.get("dimensions", []),
            }
            
            if not completeness_result["is_complete"]:
                question_result = await self.skill_runner.run(
                    "devsmart.requirement.generate-next-question",
                    {
                        "gap_analysis": analyze_result.output,
                        "conversation": all_conversations,
                    },
                    context,
                )
                assistant_response["content"] = question_result.output.get("question", assistant_response["content"])
                
        except Exception as e:
            from services.template_service import TemplateService
            
            template_service = TemplateService()
            template_weights = {}
            if template_id:
                template = template_service.get_template(template_id)
                if template and template.get("dimensions"):
                    template_weights = template["dimensions"]
            
            calculator = CompletenessCalculator(template_weights)
            completeness_result = calculator.calculate(all_conversations)

        # 6. 保存助手消息（过滤 <think> 标签）
        content = assistant_response["content"]
        if "<think>" in content:
            content = content.split("</think>")[-1].strip()
        
        assistant_message = Conversation(
            project_id=project_id,
            phase=phase,
            role="assistant",
            content=content,
            token_count=self._estimate_tokens(content),
            completeness_score=completeness_result["total_score"],
            created_at=datetime.utcnow()
        )
        self.db.add(assistant_message)
        await self.db.commit()
        await self.db.refresh(assistant_message)

        # 7. 检查是否需要生成摘要
        await self._check_and_generate_summary(project_id, phase)

        return {
            "user_message": user_message,
            "assistant_message": assistant_message,
            "completeness_score": completeness_result["total_score"],
            "is_ready_for_prd": completeness_result["is_complete"]
        }

    async def _get_rag_context(
        self,
        project_id: str,
        user_input: str,
        project: Optional[Project] = None
    ) -> List[Dict]:
        """
        获取 RAG 上下文（长期记忆 + 中期记忆）

        Args:
            project_id: 项目 ID
            user_input: 用户当前输入（用于 RAG 检索）
            project: 项目对象（用于降级回退时获取 onboarding_data）

        Returns:
            RAG 上下文列表
        """
        context = []
        rag_service = RAGService()

        # 1. 长期记忆：RAG 检索项目知识库
        rag_has_results = False
        if user_input:
            long_term_results = await rag_service.query_long_term(project_id, user_input)
            if long_term_results:
                rag_has_results = True
                for result in long_term_results:
                    doc_type = result["metadata"].get("type", "文档")
                    context.append({
                        "role": "system",
                        "content": f"【项目知识 - {doc_type}】\n{result['content']}"
                    })

        # 降级回退：如果 RAG 没有返回结果，使用 onboarding_data 作为系统提示
        if not rag_has_results and project and project.onboarding_data:
            system_prompt = self._format_onboarding_as_system_prompt(project.onboarding_data)
            context.append({
                "role": "system",
                "content": system_prompt
            })

        # 2. 中期记忆：RAG 检索对话摘要
        if user_input:
            medium_term_results = await rag_service.query_medium_term(project_id, user_input)
            for result in medium_term_results:
                context.append({
                    "role": "system",
                    "content": f"【历史对话摘要】\n{result['content']}"
                })

        return context

    async def _get_conversation_context(
        self,
        project_id: str,
        phase: str,
        user_input: str = "",
        project: Optional[Project] = None
    ) -> List[Dict]:
        """
        获取对话上下文（短期记忆）

        Args:
            project_id: 项目 ID
            phase: 阶段
            user_input: 用户当前输入
            project: 项目对象

        Returns:
            对话历史列表（短期记忆）
        """
        context = []

        # 短期记忆：最近 N 轮对话
        short_term_limit = settings.conversation_short_term_limit
        recent_query = select(Conversation).where(
            Conversation.project_id == project_id,
            Conversation.phase == phase
        ).order_by(Conversation.created_at.desc()).limit(short_term_limit)
        recent_result = await self.db.execute(recent_query)
        recent_conversations = recent_result.scalars().all()

        for conv in reversed(recent_conversations):
            context.append({
                "role": conv.role,
                "content": conv.content
            })

        return context

    def _format_onboarding_as_system_prompt(self, onboarding_data: Dict) -> str:
        """将 onboarding_data 格式化为系统提示"""
        parts = [
            "【项目背景信息】",
            f"需求描述：{onboarding_data.get('requirement_description', '未提供')}",
            f"后端技术：{onboarding_data.get('backend_tech', '未选择')}",
            f"前端技术：{onboarding_data.get('frontend_tech', '未选择')}",
            f"数据库：{onboarding_data.get('database', '未选择')}",
            f"部署形式：{onboarding_data.get('deployment', '未选择')}",
            "",
            "请基于以上项目背景进行回答。"
        ]
        return "\n".join(parts)

    async def _generate_llm_response(
        self,
        conversation_history: List[Dict],
        user_input: str,
        project_name: str
    ) -> Dict:
        """
        生成 LLM 回复

        Args:
            conversation_history: 对话历史
            user_input: 用户输入
            project_name: 项目名称

        Returns:
            {"content": "回复内容"}
        """
        # 获取 LLM 配置
        settings_service = SettingsService(self.db)
        llm_config = await settings_service.get_effective_llm_config()
        client = LLMClient(llm_config)

        # 构建消息列表
        messages = conversation_history + [{"role": "user", "content": user_input}]

        # 如果是第一次对话（只有系统提示），使用追问策略生成初始问题
        if len([m for m in conversation_history if m["role"] != "system"]) == 0:
            question_result = self.questioning_strategy.generate_next_question(
                [{"role": "user", "content": user_input}],
                project_name
            )
            return {"content": question_result["question"]}

        # 否则调用 LLM 生成回复
        try:
            response = await client.chat(messages)
            return {"content": response["content"]}
        except Exception as e:
            # 如果 LLM 调用失败，使用追问策略作为备用
            question_result = self.questioning_strategy.generate_next_question(
                conversation_history + [{"role": "user", "content": user_input}],
                project_name
            )
            return {"content": question_result["question"]}

    async def _check_and_generate_summary(
        self,
        project_id: str,
        phase: str
    ):
        """
        检查是否需要生成对话摘要

        Args:
            project_id: 项目 ID
            phase: 阶段
        """
        # 获取当前对话总数
        count_query = select(Conversation).where(
            Conversation.project_id == project_id,
            Conversation.phase == phase
        )
        count_result = await self.db.execute(count_query)
        all_conversations = count_result.scalars().all()

        # 检查是否达到摘要触发条件
        trigger_interval = settings.summary_trigger_interval
        should_generate_summary = len(all_conversations) % trigger_interval == 0

        if should_generate_summary:
            # 获取最近的对话用于生成摘要
            recent_conversations = all_conversations[-trigger_interval:]
            conversation_list = [
                {"role": c.role, "content": c.content}
                for c in recent_conversations
            ]

            # 调用 LLM 生成摘要
            settings_service = SettingsService(self.db)
            llm_config = await settings_service.get_effective_llm_config()
            client = LLMClient(llm_config)

            summary_content = await client.generate_summary(conversation_list)

            # 保存摘要到数据库
            last_conv = recent_conversations[-1]
            summary = ConversationSummary(
                project_id=project_id,
                phase=phase,
                summary=summary_content,
                covers_up_to_id=last_conv.id,
                created_at=datetime.utcnow()
            )
            self.db.add(summary)
            await self.db.commit()

            # 存入中期记忆库（RAG）
            rag_service = RAGService()
            await rag_service.add_medium_term_document(
                project_id=str(project_id),
                content=summary_content,
                metadata={
                    "type": "conversation_summary",
                    "phase": phase,
                    "covers_up_to_id": str(last_conv.id),
                    "created_at": datetime.utcnow().isoformat()
                }
            )

    async def _get_project(self, project_id: str) -> Optional[Project]:
        """获取项目信息"""
        query = select(Project).where(Project.id == project_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    def _estimate_tokens(self, text: str) -> int:
        """估算文本 token 数"""
        return len(text) // 2

    async def get_conversations(
        self,
        project_id: str,
        phase: str = "prd"
    ) -> List[Conversation]:
        """获取项目的对话历史"""
        query = select(Conversation).where(
            Conversation.project_id == project_id,
            Conversation.phase == phase
        ).order_by(Conversation.created_at.asc())
        result = await self.db.execute(query)
        return result.scalars().all()