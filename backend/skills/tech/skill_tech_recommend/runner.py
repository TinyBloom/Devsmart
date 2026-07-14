"""
skill_tech_recommend - Runner

根据 Machine PRD 推荐技术栈方案
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class TechRecommendRunner:
    """技术栈推荐 Skill Runner"""

    def __init__(self, project_dir: str, llm_service=None):
        """
        初始化 Runner

        Args:
            project_dir: 项目目录路径
            llm_service: LLM 服务实例（用于调用 LLM 生成推荐）
        """
        self.project_dir = Path(project_dir)
        self.llm_service = llm_service
        self.skill_dir = Path(__file__).parent

    async def run(self, machine_prd_path: Optional[str] = None) -> Dict[str, Any]:
        """
        执行 Skill

        Args:
            machine_prd_path: Machine PRD 文件路径，默认使用项目目录下的 docs/machine_prd.yaml

        Returns:
            执行结果，包含 status、message 和生成的文件路径
        """
        try:
            # 1. 读取 Machine PRD
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

            # 3. 生成技术推荐
            if self.llm_service:
                # 使用 LLM 生成推荐
                recommendations = await self._generate_with_llm(analysis, machine_prd)
            else:
                # 使用规则引擎生成推荐
                recommendations = self._generate_with_rules(analysis)

            # 4. 格式化输出
            tech_options = {
                "tech_options": {
                    "generated_at": self._get_timestamp(),
                    "project_name": machine_prd.get("project_name", "unknown"),
                    "analysis": analysis,
                    "recommendations": recommendations
                }
            }

            # 5. 保存输出文件
            output_file = self.project_dir / "docs" / "tech_options.yaml"
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                yaml.dump(tech_options, f, allow_unicode=True, default_flow_style=False)

            logger.info(f"技术栈推荐已保存到: {output_file}")

            return {
                "status": "SUCCESS",
                "message": f"成功生成 {len(recommendations)} 套技术方案推荐",
                "artifacts": [
                    {
                        "file_path": str(output_file),
                        "content": yaml.dump(tech_options, allow_unicode=True)
                    }
                ]
            }

        except Exception as e:
            logger.error(f"skill_tech_recommend 执行失败: {e}")
            return {
                "status": "ERROR",
                "message": f"执行失败: {str(e)}"
            }

    def _analyze_requirements(self, machine_prd: Dict) -> Dict[str, Any]:
        """分析需求特征"""
        features = machine_prd.get("features", [])
        non_functional = machine_prd.get("non_functional", {})
        integrations = machine_prd.get("integrations", [])

        # 合并所有文本用于关键词分析
        all_text = " ".join([
            " ".join(features) if isinstance(features, list) else str(features),
            " ".join(integrations) if isinstance(integrations, list) else str(integrations),
            str(non_functional)
        ]).lower()

        # 分析规模
        feature_count = len(features) if isinstance(features, list) else 0
        expected_users = non_functional.get("expected_users", "medium")
        if feature_count > 20 or expected_users == "large":
            scale = "large"
        elif feature_count > 5 or expected_users == "medium":
            scale = "medium"
        else:
            scale = "small"

        # 分析团队规模
        team_size = non_functional.get("team_size", "small")
        if team_size in ["large", "medium"]:
            team_size = "medium"

        # 分析性能要求
        perf_req = non_functional.get("performance", {})
        if perf_req.get("concurrent_users") == "high" or perf_req.get("response_time") == "ms":
            performance_level = "high"
        else:
            performance_level = "normal"

        # 分析时间压力
        timeline = non_functional.get("timeline", "normal")
        if timeline in ["urgent", "very_urgent"]:
            time_pressure = "high"
        elif timeline == "flexible":
            time_pressure = "low"
        else:
            time_pressure = "medium"

        # 检查 AI 需求
        ai_keywords = ["ai", "llm", "gpt", "chat", "nlp", "图像识别", "语音", "人工智能"]
        has_ai = any(keyword in all_text for keyword in ai_keywords)

        return {
            "scale": scale,
            "team_size": team_size,
            "performance_level": performance_level,
            "time_pressure": time_pressure,
            "has_ai": has_ai,
            "feature_count": feature_count
        }

    async def _generate_with_llm(self, analysis: Dict, machine_prd: Dict) -> list:
        """使用 LLM 生成推荐"""
        # 读取 prompt 模板
        prompt_file = self.skill_dir / "prompt_user.md"
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt_template = f.read()

        # 填充 prompt
        prompt = prompt_template.replace(
            "{machine_prd_content}",
            yaml.dump(machine_prd, allow_unicode=True)
        )

        # 调用 LLM
        response = await self.llm_service.generate(prompt)

        # 解析 LLM 响应
        # TODO: 实现更 robust 的 YAML 解析
        try:
            # 尝试从响应中提取 YAML
            if "```yaml" in response:
                yaml_content = response.split("```yaml")[1].split("```")[0]
            else:
                yaml_content = response

            parsed = yaml.safe_load(yaml_content)
            if parsed and "tech_options" in parsed:
                return parsed["tech_options"]
        except Exception as e:
            logger.warning(f"LLM 响应解析失败: {e}")

        # 解析失败时使用规则引擎
        return self._generate_with_rules(analysis)

    def _generate_with_rules(self, analysis: Dict) -> list:
        """使用规则引擎生成推荐"""
        recommendations = []

        # 基础推荐：根据 AI 需求决定
        if analysis["has_ai"]:
            recommendations.append(self._build_python_fastapi_rec(analysis))
            if analysis["scale"] != "small":
                recommendations.append(self._build_go_gin_rec(analysis))
        else:
            recommendations.append(self._build_go_gin_rec(analysis))
            if analysis["scale"] == "large" and analysis["time_pressure"] != "high":
                recommendations.append(self._build_java_spring_rec(analysis))

        # 如果规模大且时间不紧迫，补充 Quarkus
        if analysis["scale"] == "large" and len(recommendations) < 3:
            recommendations.append(self._build_java_quarkus_rec(analysis))

        # 确保至少有一个推荐
        if not recommendations:
            recommendations.append(self._build_python_fastapi_rec(analysis))

        return recommendations[:3]

    def _build_python_fastapi_rec(self, analysis: Dict) -> Dict:
        """构建 Python FastAPI 推荐"""
        rec = {
            "name": "快速原型方案",
            "description": "最适合快速交付和 AI 集成的方案",
            "backend": {
                "framework": "Python + FastAPI",
                "orm": "SQLAlchemy",
                "pros": [
                    "Python 语法简洁，开发效率极高",
                    "AI/ML 集成最方便",
                    "FastAPI 自动生成 OpenAPI 文档",
                    "异步支持好，HMR 开发体验佳"
                ],
                "cons": [
                    "性能不如 Go/Rust",
                    "GIL 限制多线程性能",
                    "运行时错误，只有执行到才报错"
                ],
                "complexity": "低",
                "performance": "中",
                "time_to_market": "很快"
            },
            "frontend": {
                "framework": "React + Vite",
                "ui_library": "shadcn/ui"
            },
            "database": {
                "primary": "PostgreSQL",
                "cache": "Redis"
            },
            "deployment": {
                "method": "Kubernetes + Helm"
            },
            "cicd": {
                "tool": "GitHub Actions"
            },
            "reason": "",
            "tradeoffs": "",
            "risk": "高并发场景可能需要额外优化",
            "suitability_score": 0
        }

        # 根据分析结果调整推荐理由和评分
        reasons = []
        score = 70

        if analysis["has_ai"]:
            reasons.append("AI 集成需求强烈，Python 是 AI/ML 领域的首选语言")
            score += 15
        if analysis["time_pressure"] == "high":
            reasons.append("时间紧迫，需要快速交付")
            score += 10
        if analysis["scale"] == "small":
            reasons.append("小规模项目，FastAPI 可以快速完成开发")
            score += 5

        rec["reason"] = "；".join(reasons) if reasons else "综合评估后的推荐方案"
        rec["tradeoffs"] = f"""优点：开发效率高，AI 集成方便，FastAPI 自动生成 OpenAPI 文档
缺点：性能中等，GIL 限制多线程
复杂度：低
性能：中
上市时间：很快"""
        rec["suitability_score"] = min(score, 100)

        return rec

    def _build_go_gin_rec(self, analysis: Dict) -> Dict:
        """构建 Go Gin 推荐"""
        rec = {
            "name": "高性能微服务方案",
            "description": "平衡开发效率和运行性能的方案",
            "backend": {
                "framework": "Go + Gin",
                "orm": "GORM",
                "pros": [
                    "语言简洁，学习曲线平缓",
                    "并发模型优雅 (goroutine)",
                    "编译快速，部署简单 (单个二进制)",
                    "内存占用低，性能优秀"
                ],
                "cons": [
                    "泛型支持较晚，某些场景代码较啰嗦",
                    "错误处理需要手动处理",
                    "ORM 生态不如 Java/Python 成熟"
                ],
                "complexity": "低",
                "performance": "高",
                "time_to_market": "快"
            },
            "frontend": {
                "framework": "React + Vite",
                "ui_library": "shadcn/ui"
            },
            "database": {
                "primary": "PostgreSQL",
                "cache": "Redis"
            },
            "deployment": {
                "method": "Kubernetes + Helm"
            },
            "cicd": {
                "tool": "GitHub Actions"
            },
            "reason": "",
            "tradeoffs": "",
            "risk": "复杂业务逻辑可能需要更多代码",
            "suitability_score": 0
        }

        reasons = []
        score = 75

        if analysis["performance_level"] == "high":
            reasons.append("性能要求高，Go 语言性能优异")
            score += 10
        if analysis["time_pressure"] == "medium":
            reasons.append("Go 语言简洁，兼顾开发效率和运行性能")
            score += 5
        reasons.append("微服务友好，部署简单")

        rec["reason"] = "；".join(reasons) if reasons else "综合评估后的推荐方案"
        rec["tradeoffs"] = f"""优点：性能优秀，并发模型优雅，部署简单
缺点：ORM 生态不成熟，错误处理繁琐
复杂度：低
性能：高
上市时间：快"""
        rec["suitability_score"] = min(score, 100)

        return rec

    def _build_java_spring_rec(self, analysis: Dict) -> Dict:
        """构建 Java Spring 推荐"""
        rec = {
            "name": "企业级稳定方案",
            "description": "适合大型复杂业务系统的方案",
            "backend": {
                "framework": "Java + Spring Boot",
                "orm": "Spring Data JPA",
                "pros": [
                    "企业级成熟度，生态极其完善",
                    "框架稳定，大量生产验证",
                    "文档、社区、招聘市场丰富",
                    "Spring Cloud 微服务生态完整"
                ],
                "cons": [
                    "启动速度慢，开发阶段编译时间长",
                    "内存占用较高",
                    "配置相对繁琐"
                ],
                "complexity": "中",
                "performance": "中",
                "time_to_market": "中"
            },
            "frontend": {
                "framework": "React + Vite",
                "ui_library": "Ant Design"
            },
            "database": {
                "primary": "PostgreSQL",
                "cache": "Redis"
            },
            "deployment": {
                "method": "Spring Cloud"
            },
            "cicd": {
                "tool": "Jenkins"
            },
            "reason": "",
            "tradeoffs": "",
            "risk": "开发效率相对较低",
            "suitability_score": 0
        }

        reasons = []
        score = 70

        if analysis["scale"] == "large":
            reasons.append("大规模系统，企业级稳定性重要")
            score += 15
        reasons.append("Spring 生态最完善，社区支持好")

        rec["reason"] = "；".join(reasons) if reasons else "综合评估后的推荐方案"
        rec["tradeoffs"] = f"""优点：企业级稳定性，生态完善，微服务支持好
缺点：启动慢，内存占用高，配置繁琐
复杂度：中
性能：中
上市时间：中"""
        rec["suitability_score"] = min(score, 100)

        return rec

    def _build_java_quarkus_rec(self, analysis: Dict) -> Dict:
        """构建 Java Quarkus 推荐"""
        rec = {
            "name": "云原生 Java 方案",
            "description": "现代化云原生 Java 开发体验",
            "backend": {
                "framework": "Java + Quarkus",
                "orm": "Panache",
                "pros": [
                    "GraalVM 原生编译，启动极快 (ms 级)",
                    "低内存占用，适合容器化",
                    "编译时元编程，减少运行时反射",
                    "保留 Spring 生态，熟悉 Spring 的开发者易上手"
                ],
                "cons": [
                    "相对较新，生态不如 Spring Boot 完善",
                    "部分 Spring 特性需要替换实现"
                ],
                "complexity": "中",
                "performance": "高",
                "time_to_market": "快"
            },
            "frontend": {
                "framework": "React + Vite",
                "ui_library": "shadcn/ui"
            },
            "database": {
                "primary": "PostgreSQL",
                "cache": "Redis"
            },
            "deployment": {
                "method": "Kubernetes + Helm"
            },
            "cicd": {
                "tool": "GitHub Actions"
            },
            "reason": "",
            "tradeoffs": "",
            "risk": "生态相对年轻，某些库可能不完善",
            "suitability_score": 0
        }

        reasons = [
            "云原生部署，Quarkus 启动极快",
            "内存占用低，适合容器化"
        ]

        rec["reason"] = "；".join(reasons)
        rec["tradeoffs"] = f"""优点：启动极快，内存占用低，云原生友好
缺点：生态相对年轻
复杂度：中
性能：高
上市时间：快"""
        rec["suitability_score"] = 75

        return rec

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"


# 作为独立脚本运行时
if __name__ == "__main__":
    import asyncio
    import sys

    async def main():
        if len(sys.argv) < 2:
            print("用法: python runner.py <project_dir>")
            sys.exit(1)

        project_dir = sys.argv[1]
        runner = TechRecommendRunner(project_dir)
        result = await runner.run()
        print(yaml.dump(result, allow_unicode=True))

    asyncio.run(main())
