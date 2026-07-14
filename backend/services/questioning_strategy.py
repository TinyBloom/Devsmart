"""
追问策略实现
根据 DevSmart_PRD_v1.0.md Section 5.1.2 定义
"""

from typing import List, Dict, Optional
from services.completeness_calculator import CompletenessCalculator


class QuestioningStrategy:
    """LLM 追问策略"""

    # 各维度的追问模板
    QUESTION_TEMPLATES = {
        "核心功能": {
            "initial": "这个应用的核心功能是什么？用户主要用它来做什么？",
            "followup": [
                "能详细描述一下{功能}功能吗？用户具体怎么操作？",
                "除了{已提到的功能}，还有其他主要功能模块吗？",
                "这些功能中，哪个是最重要的核心功能？",
                "用户在使用{功能}时，期望达到什么目标？"
            ]
        },
        "用户角色": {
            "initial": "这个应用的目标用户是谁？",
            "followup": [
                "不同类型的用户在使用这个系统时，权限和功能有什么区别？",
                "用户数量大概有多少？主要活跃在什么时间段？",
                "用户是如何注册和登录的？",
                "管理员和普通用户的主要区别是什么？"
            ]
        },
        "数据实体": {
            "initial": "这个应用主要处理哪些数据？有哪些核心实体？",
            "followup": [
                "{实体}包含哪些字段？哪些是必填的？",
                "{实体}之间有什么关联关系？",
                "用户可以创建、编辑、删除哪些数据？",
                "数据需要长期保存吗？有历史记录需求吗？"
            ]
        },
        "非功能需求": {
            "initial": "这个应用对性能和安全有什么要求？",
            "followup": [
                "预期的并发用户数是多少？高峰期流量如何？",
                "对响应时间有什么要求？用户能接受多长的等待？",
                "数据安全级别如何？需要加密存储吗？",
                "系统可用性要求是 7x24 小时吗？允许停机维护吗？"
            ]
        },
        "外部集成": {
            "initial": "这个应用需要对接哪些外部服务或第三方平台？",
            "followup": [
                "支付功能用哪个平台？微信支付、支付宝还是其他？",
                "需要发送邮件或短信通知吗？",
                "有文件存储需求吗？使用云存储还是本地存储？",
                "需要集成地图、推送或其他第三方 SDK 吗？"
            ]
        }
    }

    def __init__(self):
        self.calculator = CompletenessCalculator()

    def generate_next_question(
        self,
        conversations: List[Dict],
        project_name: str
    ) -> Dict:
        """
        生成下一个追问

        Args:
            conversations: 对话历史列表
            project_name: 项目名称

        Returns:
            {
                "question": "追问内容",
                "dimension": "追问维度",
                "completeness_score": 0-100,
                "is_ready_for_prd": True/False
            }
        """
        # 计算完整度
        result = self.calculator.calculate(conversations)
        score = result["total_score"]

        # 如果完整度 >= 80，提示用户确认生成 PRD
        if score >= 80.0:
            return {
                "question": f"需求已经比较完整了（完整度 {score}%）。我可以帮你生成一份详细的 PRD 文档了，确认开始生成吗？",
                "dimension": "confirmation",
                "completeness_score": score,
                "is_ready_for_prd": True
            }

        # 获取下一个追问维度
        next_dimension = self.calculator.get_next_question_dimension(conversations)

        # 根据对话历史选择合适的追问模板
        question = self._select_question_template(
            next_dimension,
            conversations,
            project_name
        )

        return {
            "question": question,
            "dimension": next_dimension,
            "completeness_score": score,
            "is_ready_for_prd": False
        }

    def _select_question_template(
        self,
        dimension: str,
        conversations: List[Dict],
        project_name: str
    ) -> str:
        """
        选择合适的追问模板

        Args:
            dimension: 追问维度
            conversations: 对话历史列表
            project_name: 项目名称

        Returns:
            追问内容
        """
        templates = self.QUESTION_TEMPLATES.get(dimension, {})
        
        # 检查该维度是否已经被问过
        dimension_mentioned = False
        for conv in conversations:
            if conv.get("role") == "assistant":
                content = conv.get("content", "").lower()
                if any(keyword in content for keyword in self.calculator.DIMENSIONS[dimension]["keywords"]):
                    dimension_mentioned = True
                    break

        # 如果该维度第一次追问，使用初始模板
        if not dimension_mentioned or "initial" not in templates:
            return templates.get("initial", f"请告诉我关于{dimension}的更多细节。")

        # 否则使用追问模板
        followup_questions = templates.get("followup", [])
        if followup_questions:
            # 选择一个合适的追问（随机或基于历史内容选择）
            # 这里简化处理：轮流使用追问模板
            question_count = sum(1 for conv in conversations if conv.get("role") == "assistant")
            selected_index = (question_count - 1) % len(followup_questions)
            return followup_questions[selected_index]

        return f"能再详细说说{dimension}方面的需求吗？"

    def analyze_user_input(self, user_input: str, conversations: List[Dict]) -> Dict:
        """
        分析用户输入，提取关键信息

        Args:
            user_input: 用户输入内容
            conversations: 对话历史列表

        Returns:
            {
                "mentioned_dimensions": ["维度1", "维度2"],
                "new_information": True/False
            }
        """
        mentioned_dimensions = []

        for dimension, config in self.calculator.DIMENSIONS.items():
            for keyword in config["keywords"]:
                if keyword.lower() in user_input.lower():
                    mentioned_dimensions.append(dimension)
                    break

        # 检查是否提供了新信息
        previous_content = " ".join([c.get("content", "") for c in conversations])
        new_information = any(
            keyword.lower() not in previous_content.lower()
            for keyword in user_input.split()
        )

        return {
            "mentioned_dimensions": mentioned_dimensions,
            "new_information": new_information
        }