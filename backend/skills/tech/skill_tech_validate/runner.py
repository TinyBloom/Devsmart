"""
skill_tech_validate - Runner

验证用户选择的技术栈是否合理
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class TechValidateRunner:
    """技术栈验证 Skill Runner"""

    # 验证规则定义
    VALIDATION_RULES = {
        "backend": [
            {
                "id": "ai_mismatch",
                "condition": lambda analysis, selection: analysis.get("has_ai") and selection.get("backend") != "python_fastapi",
                "severity": "warning",
                "message": "检测到 AI 相关需求，建议考虑 Python 作为后端语言",
                "suggestion": "如果团队有 Python 经验，建议使用 Python FastAPI 以获得更好的 AI 集成体验"
            },
            {
                "id": "rust_small_project",
                "condition": lambda analysis, selection: selection.get("backend") == "rust_actix" and analysis.get("scale") == "small",
                "severity": "high",
                "message": "Rust 学习曲线陡峭，编译时间长，不适合快速原型开发",
                "suggestion": "如果团队没有 Rust 经验，建议选择 Go + Gin 或 Python + FastAPI"
            },
            {
                "id": "python_large_scale",
                "condition": lambda analysis, selection: selection.get("backend") == "python_fastapi" and analysis.get("scale") == "large",
                "severity": "medium",
                "message": "Python FastAPI 在超大规模系统中的性能可能不足",
                "suggestion": "考虑使用 Go + Gin 或 Java Spring Boot 以获得更好的性能"
            },
            {
                "id": "high_concurrency_python",
                "condition": lambda analysis, selection: analysis.get("performance_level") == "high" and selection.get("backend") == "python_fastapi",
                "severity": "high",
                "message": "Python (GIL) 在高并发场景下性能受限",
                "suggestion": "考虑使用 Go + Gin 或 Rust + Actix 以满足性能需求"
            },
            {
                "id": "java_urgent_timeline",
                "condition": lambda analysis, selection: selection.get("backend") in ["java_spring", "java_quarkus"] and analysis.get("time_pressure") == "high",
                "severity": "medium",
                "message": "Java 开发周期相对较长，可能影响紧急项目的交付时间",
                "suggestion": "如果时间紧迫，建议考虑 Go + Gin 或 Python + FastAPI"
            }
        ],
        "database": [
            {
                "id": "elasticsearch_overkill",
                "condition": lambda analysis, selection: selection.get("database") == "elasticsearch" and analysis.get("feature_count", 0) < 5,
                "severity": "low",
                "message": "Elasticsearch 资源消耗大，运维复杂，简单项目可能不需要",
                "suggestion": "如果搜索不是核心需求，可以先使用 PostgreSQL 的全文搜索功能"
            },
            {
                "id": "mongodb_transaction",
                "condition": lambda analysis, selection: selection.get("database") == "mongodb" and analysis.get("needs_transaction", False),
                "severity": "high",
                "message": "MongoDB 事务能力有限，强一致性场景不推荐",
                "suggestion": "如果需要强事务支持，建议使用 PostgreSQL"
            }
        ],
        "deployment": [
            {
                "id": "k8s_small_project",
                "condition": lambda analysis, selection: "kubernetes" in selection.get("deployment", "").lower() and analysis.get("feature_count", 0) < 5,
                "severity": "low",
                "message": "Kubernetes 复杂度较高，对于简单项目可能过度设计",
                "suggestion": "可以考虑简单的 Docker + Docker Compose 部署"
            },
            {
                "id": "spring_cloud_non_java",
                "condition": lambda analysis, selection: selection.get("deployment") == "spring_cloud" and selection.get("backend") not in ["java_spring", "java_quarkus"],
                "severity": "high",
                "message": "Spring Cloud 主要针对 Java 技术栈",
                "suggestion": "如果选择 Spring Cloud 作为部署方式，建议后端使用 Java Spring Boot"
            }
        ]
    }

    # 兼容性矩阵
    COMPATIBILITY_MATRIX = {
        ("react_vite", "python_fastapi"): True,
        ("react_vite", "go_gin"): True,
        ("react_vite", "java_spring"): True,
        ("react_vite", "java_quarkus"): True,
        ("react_vite", "rust_actix"): True,
        ("vue_vite", "python_fastapi"): True,
        ("vue_vite", "go_gin"): True,
        ("vue_vite", "java_spring"): True,
        ("vue_vite", "java_quarkus"): True,
        ("vue_vite", "rust_actix"): True,
        ("spring_cloud", "java_spring"): True,
        ("spring_cloud", "java_quarkus"): True,
        ("spring_cloud", "python_fastapi"): False,
        ("spring_cloud", "go_gin"): False,
        ("spring_cloud", "rust_actix"): False,
    }

    def __init__(self, project_dir: str, llm_service=None):
        """
        初始化 Runner

        Args:
            project_dir: 项目目录路径
            llm_service: LLM 服务实例
        """
        self.project_dir = Path(project_dir)
        self.llm_service = llm_service
        self.skill_dir = Path(__file__).parent

    async def run(
        self,
        tech_selection: Dict[str, Any],
        machine_prd_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行 Skill

        Args:
            tech_selection: 用户选择的技术栈
            machine_prd_path: Machine PRD 文件路径

        Returns:
            执行结果
        """
        try:
            # 1. 加载 Machine PRD
            if machine_prd_path:
                prd_file = Path(machine_prd_path)
            else:
                prd_file = self.project_dir / "docs" / "machine_prd.yaml"

            if not prd_file.exists():
                return {
                    "status": "ERROR",
                    "message": f"Machine PRD 文件不存在: {prd_file}"
                }

            with open(prd_file, 'r', encoding='utf-8') as f:
                machine_prd = yaml.safe_load(f)

            # 2. 分析需求特征
            analysis = self._analyze_requirements(machine_prd)

            # 3. 执行验证
            warnings = []
            suggestions = []

            # 验证后端
            warnings.extend(self._validate_category("backend", analysis, tech_selection))

            # 验证数据库
            warnings.extend(self._validate_category("database", analysis, tech_selection))

            # 验证部署
            warnings.extend(self._validate_category("deployment", analysis, tech_selection))

            # 检查兼容性
            compatibility = self._check_compatibility(tech_selection)

            # 4. 生成建议
            suggestions.extend(self._generate_suggestions(analysis, tech_selection, warnings))

            # 5. 确定状态
            status = self._determine_status(warnings)

            # 6. 生成报告
            report = {
                "validation_report": {
                    "generated_at": self._get_timestamp(),
                    "project_name": machine_prd.get("project_name", "unknown"),
                    "status": status,
                    "summary": self._build_summary(warnings, suggestions),
                    "warnings": warnings,
                    "suggestions": suggestions,
                    "compatibility_matrix": compatibility
                }
            }

            # 7. 保存报告
            output_file = self.project_dir / "docs" / "tech_validation.yaml"
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                yaml.dump(report, f, allow_unicode=True, default_flow_style=False)

            logger.info(f"技术栈验证报告已保存到: {output_file}")

            return {
                "status": "SUCCESS",
                "message": f"验证完成，状态: {status}",
                "validation": report["validation_report"],
                "artifacts": [
                    {
                        "file_path": str(output_file),
                        "content": yaml.dump(report, allow_unicode=True)
                    }
                ]
            }

        except Exception as e:
            logger.error(f"skill_tech_validate 执行失败: {e}")
            return {
                "status": "ERROR",
                "message": f"执行失败: {str(e)}"
            }

    def _analyze_requirements(self, machine_prd: Dict) -> Dict[str, Any]:
        """分析需求特征"""
        features = machine_prd.get("features", [])
        non_functional = machine_prd.get("non_functional", {})
        integrations = machine_prd.get("integrations", [])

        all_text = " ".join([
            " ".join(features) if isinstance(features, list) else str(features),
            " ".join(integrations) if isinstance(integrations, list) else str(integrations),
            str(non_functional)
        ]).lower()

        # 规模
        feature_count = len(features) if isinstance(features, list) else 0
        expected_users = non_functional.get("expected_users", "medium")
        if feature_count > 20 or expected_users == "large":
            scale = "large"
        elif feature_count > 5 or expected_users == "medium":
            scale = "medium"
        else:
            scale = "small"

        # 性能要求
        perf_req = non_functional.get("performance", {})
        performance_level = "high" if perf_req.get("concurrent_users") == "high" else "normal"

        # 时间压力
        timeline = non_functional.get("timeline", "normal")
        time_pressure = "high" if timeline in ["urgent", "very_urgent"] else "normal"

        # AI 需求
        ai_keywords = ["ai", "llm", "gpt", "chat", "nlp", "图像识别", "语音", "人工智能"]
        has_ai = any(keyword in all_text for keyword in ai_keywords)

        return {
            "scale": scale,
            "feature_count": feature_count,
            "performance_level": performance_level,
            "time_pressure": time_pressure,
            "has_ai": has_ai,
            "needs_transaction": non_functional.get("needs_transaction", False)
        }

    def _validate_category(
        self,
        category: str,
        analysis: Dict[str, Any],
        selection: Dict[str, Any]
    ) -> List[Dict]:
        """验证特定类别"""
        warnings = []
        rules = self.VALIDATION_RULES.get(category, [])

        for rule in rules:
            try:
                if rule["condition"](analysis, selection):
                    warnings.append({
                        "id": rule["id"],
                        "severity": rule["severity"],
                        "message": rule["message"],
                        "suggestion": rule.get("suggestion", "")
                    })
            except Exception as e:
                logger.warning(f"验证规则 {rule['id']} 执行失败: {e}")

        return warnings

    def _check_compatibility(self, selection: Dict[str, Any]) -> Dict[str, Any]:
        """检查技术栈兼容性"""
        backend = selection.get("backend", "")
        frontend = selection.get("frontend", "")
        deployment = selection.get("deployment", "")

        # 前后端兼容性
        if frontend and backend:
            be_fe_key = (frontend, backend)
            backend_frontend = self.COMPATIBILITY_MATRIX.get(be_fe_key, True)
        else:
            backend_frontend = True

        # 后端与部署兼容性
        if deployment and backend:
            deploy_key = (deployment, backend)
            backend_deployment = self.COMPATIBILITY_MATRIX.get(deploy_key, True)
        else:
            backend_deployment = True

        # 后端与数据库通常都兼容
        backend_database = True

        all_compatible = backend_frontend and backend_deployment and backend_database

        return {
            "backend_frontend": "compatible" if backend_frontend else "incompatible",
            "backend_database": "compatible" if backend_database else "incompatible",
            "backend_deployment": "compatible" if backend_deployment else "incompatible",
            "all_compatible": all_compatible
        }

    def _generate_suggestions(
        self,
        analysis: Dict[str, Any],
        selection: Dict[str, Any],
        warnings: List[Dict]
    ) -> List[Dict]:
        """生成建议"""
        suggestions = []

        # 如果有 AI 需求但没选 Python
        if analysis["has_ai"] and selection.get("backend") != "python_fastapi":
            existing_ids = [w["id"] for w in warnings]
            if "ai_mismatch" not in existing_ids:
                suggestions.append({
                    "message": "检测到 AI 相关需求，建议考虑 Python 作为后端语言以获得更好的 AI 集成体验"
                })

        # 如果选了 Rust 但团队可能不熟悉
        if selection.get("backend") == "rust_actix":
            suggestions.append({
                "message": "Rust 是一门强大的语言，但学习曲线较陡，建议确保团队有足够的学习时间和意愿"
            })

        return suggestions

    def _determine_status(self, warnings: List[Dict]) -> str:
        """确定验证状态"""
        if not warnings:
            return "passed"

        # 有高严重程度的警告
        if any(w["severity"] == "high" for w in warnings):
            return "error"

        return "warning"

    def _build_summary(self, warnings: List[Dict], suggestions: List[Dict]) -> str:
        """构建总结"""
        high_count = sum(1 for w in warnings if w["severity"] == "high")
        medium_count = sum(1 for w in warnings if w["severity"] == "medium")
        low_count = sum(1 for w in warnings if w["severity"] == "low")

        parts = []
        if high_count > 0:
            parts.append(f"{high_count} 个高严重程度问题")
        if medium_count > 0:
            parts.append(f"{medium_count} 个中严重程度问题")
        if low_count > 0:
            parts.append(f"{low_count} 个低严重程度问题")

        if not parts:
            return "技术栈选择合理，未发现明显问题"

        summary = "发现 " + "，".join(parts)
        if suggestions:
            summary += f"，另有 {len(suggestions)} 条建议"
        return summary

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        return datetime.utcnow().isoformat() + "Z"


# 作为独立脚本运行时
if __name__ == "__main__":
    import asyncio
    import sys

    async def main():
        if len(sys.argv) < 2:
            print("用法: python runner.py <tech_selection_json>")
            sys.exit(1)

        selection = json.loads(sys.argv[1])
        runner = TechValidateRunner(".")
        result = await runner.run(selection)
        print(yaml.dump(result, allow_unicode=True))

    asyncio.run(main())
