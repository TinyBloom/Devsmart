"""
需求完整度评分算法
根据 DevSmart_PRD_v1.0.md Section 5.1.3 定义
支持模板维度权重
"""

import re
from typing import List, Dict, Optional


class CompletenessCalculator:
    """需求完整度评分器"""

    # 默认评分维度配置
    DEFAULT_DIMENSIONS = {
        "核心功能": {
            "weight": 0.30,
            "keywords": [
                "功能", "模块", "feature", "用户故事", "特性",
                "可以", "能够", "支持", "提供", "实现",
                "添加", "编辑", "删除", "查看", "搜索", "管理"
            ]
        },
        "用户角色": {
            "weight": 0.15,
            "keywords": [
                "用户", "角色", "admin", "user", "customer",
                "管理员", "普通用户", "访客", "会员", "游客",
                "谁", "人群", "受众", "target"
            ]
        },
        "数据实体": {
            "weight": 0.25,
            "keywords": [
                "数据", "实体", "表", "字段", "model", "schema",
                "数据库", "存储", "记录", "信息", "属性",
                "名称", "类型", "必填", "关系", "关联"
            ]
        },
        "非功能需求": {
            "weight": 0.15,
            "keywords": [
                "并发", "性能", "安全", "响应时间", "吞吐量",
                "延迟", "扩展性", "稳定性", "可用性",
                "认证", "授权", "加密", "权限", "防护"
            ]
        },
        "外部集成": {
            "weight": 0.15,
            "keywords": [
                "集成", "API", "第三方", "支付", "邮件",
                "短信", "推送", "地图", "存储", "云服务",
                "对接", "接入", "外部", "oauth", "sdk"
            ]
        }
    }

    def __init__(self, custom_weights: Optional[Dict[str, float]] = None):
        """
        初始化完整度评分器

        Args:
            custom_weights: 自定义维度权重（可选），例如 {"core_features": 30, "user_roles": 15}
        """
        self._dimensions = self.DEFAULT_DIMENSIONS.copy()
        
        # 如果提供了自定义权重，应用它们
        if custom_weights:
            weight_mapping = {
                "core_features": "核心功能",
                "user_roles": "用户角色",
                "data_entities": "数据实体",
                "non_functional": "非功能需求",
                "integrations": "外部集成"
            }
            
            for key, weight in custom_weights.items():
                dimension_name = weight_mapping.get(key)
                if dimension_name and dimension_name in self._dimensions:
                    self._dimensions[dimension_name]["weight"] = weight / 100.0

    def calculate(self, conversations: List[Dict]) -> float:
        """
        计算需求完整度分数

        Args:
            conversations: 对话历史列表 [{"role": "user/assistant", "content": "..."}]

        Returns:
            完整度分数（0-100）
        """
        # 合并所有对话内容
        all_content = ""
        for conv in conversations:
            if conv.get("role") in ["user", "assistant"]:
                all_content += conv.get("content", "") + " "

        # 计算各维度得分
        dimension_scores = {}
        total_score = 0.0

        for dimension, config in self._dimensions.items():
            dimension_score = self._calculate_dimension_score(all_content, config["keywords"])
            weighted_score = dimension_score * config["weight"]
            dimension_scores[dimension] = {
                "raw_score": dimension_score,
                "weighted_score": weighted_score
            }
            total_score += weighted_score

        return {
            "total_score": round(total_score * 100, 2),
            "dimension_scores": dimension_scores,
            "is_complete": total_score * 100 >= 80.0
        }

    def _calculate_dimension_score(self, content: str, keywords: List[str]) -> float:
        """
        计算单个维度的得分

        Args:
            content: 文本内容
            keywords: 该维度的关键词列表

        Returns:
            该维度得分（0-1）
        """
        content_lower = content.lower()

        # 统计关键词匹配数量
        matched_keywords = []
        for keyword in keywords:
            if keyword.lower() in content_lower:
                matched_keywords.append(keyword)

        # 如果没有匹配到任何关键词，返回0分
        if len(matched_keywords) == 0:
            return 0.0

        # 计算匹配率（匹配关键词数 / 总关键词数）
        match_ratio = len(matched_keywords) / len(keywords)

        # 应用饱和函数：匹配超过 50% 的关键词即可达到该维度满分
        saturated_score = min(match_ratio * 2, 1.0)

        return saturated_score

    def get_missing_dimensions(self, conversations: List[Dict]) -> List[str]:
        """
        获取缺失或不充分的维度列表

        Args:
            conversations: 对话历史列表

        Returns:
            缺失维度列表（按权重排序）
        """
        result = self.calculate(conversations)
        missing = []

        for dimension, scores in result["dimension_scores"].items():
            # 如果该维度得分低于阈值（30%），认为缺失或不充分
            if scores["weighted_score"] < 0.30 * self._dimensions[dimension]["weight"]:
                missing.append(dimension)

        # 按权重排序
        missing.sort(key=lambda d: self._dimensions[d]["weight"], reverse=True)

        return missing

    def get_next_question_dimension(self, conversations: List[Dict]) -> str:
        """
        获取下一个应该追问的维度

        Args:
            conversations: 对话历史列表

        Returns:
            下一个追问维度
        """
        missing = self.get_missing_dimensions(conversations)

        if missing:
            return missing[0]

        # 如果没有缺失维度，但完整度不够，返回得分最低的维度
        result = self.calculate(conversations)
        lowest_dimension = min(
            result["dimension_scores"].items(),
            key=lambda x: x[1]["weighted_score"]
        )[0]

        return lowest_dimension