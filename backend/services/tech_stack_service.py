"""
技术栈推荐服务
根据 Machine PRD 内容，推荐 1-3 套技术方案
"""

from typing import Optional
import json


# 技术栈选项库 - 包含详细权衡说明
TECH_STACK_LIBRARY = {
    "backend": {
        "rust_actix": {
            "name": "Rust + Actix-web",
            "framework": "actix-web",
            "orm": "sea-orm",
            "pros": [
                "极高的运行时性能，内存安全，无 GC 停顿",
                "编译时检查，消除大量运行时错误",
                "并发模型优秀，适合高并发场景",
                "二进制部署，无依赖"
            ],
            "cons": [
                "编译时间长，开发迭代效率低",
                "学习曲线陡峭，团队技术储备要求高",
                "生态系统相对年轻，某些库不如 Java/Python 成熟",
                "异步生态 (async/await) 还在成熟中"
            ],
            "suitable_for": [
                "对性能要求极高的核心服务",
                "系统级基础设施组件",
                "资源受限的边缘计算场景"
            ],
            "not_suitable_for": [
                "需要快速原型验证的项目",
                "团队成员 Rust 经验不足",
                "需要大量第三方库集成的项目"
            ],
            "complexity": "高",
            "performance": "极高",
            "time_to_market": "慢"
        },
        "java_spring": {
            "name": "Java + Spring Boot",
            "framework": "Spring Boot",
            "orm": "Spring Data JPA / MyBatis",
            "pros": [
                "企业级成熟度，生态极其完善",
                "框架稳定，大量生产验证",
                "文档、社区、招聘市场丰富",
                "Spring Cloud 微服务生态完整",
                "IDE 支持极佳"
            ],
            "cons": [
                "启动速度慢，开发阶段编译时间长",
                "内存占用较高",
                "配置相对繁琐",
                "版本升级有时会带来兼容性问题"
            ],
            "suitable_for": [
                "企业级复杂业务系统",
                "需要长期维护的项目",
                "团队有 Java 经验的"
            ],
            "not_suitable_for": [
                "追求极致性能的微服务",
                "Serverless/Function as a Service 场景",
                "资源受限环境"
            ],
            "complexity": "中",
            "performance": "中",
            "time_to_market": "中"
        },
        "java_quarkus": {
            "name": "Java + Quarkus",
            "framework": "Quarkus",
            "orm": "Panache",
            "pros": [
                "GraalVM 原生编译，启动极快 (ms 级)",
                "低内存占用，适合容器化",
                "编译时元编程，减少运行时反射",
                "保留 Spring 生态，熟悉 Spring 的开发者易上手"
            ],
            "cons": [
                "相对较新，生态不如 Spring Boot 完善",
                "部分 Spring 特性需要替换实现",
                "原生编译时间仍然较长"
            ],
            "suitable_for": [
                "云原生 / Kubernetes 部署",
                "Serverless 场景",
                "微服务架构"
            ],
            "not_suitable_for": [
                "需要大量 Spring 特性的复杂应用",
                "团队完全不懂 Java"
            ],
            "complexity": "中",
            "performance": "高",
            "time_to_market": "快"
        },
        "go_gin": {
            "name": "Go + Gin/Echo",
            "framework": "Gin / Echo",
            "orm": "GORM / ent",
            "pros": [
                "语言简洁，学习曲线平缓",
                "并发模型优雅 (goroutine)，易于编写高并发服务",
                "编译快速，部署简单 (单个二进制)",
                "内存占用低，性能优秀",
                "错误处理机制清晰"
            ],
            "cons": [
                "泛型支持较晚，某些场景写起代码来较啰嗦",
                "错误处理需要手动处理，容易忽略",
                "ORM 生态不如 Java/Python 成熟",
                "缺少运行时反射，某些框架功能受限"
            ],
            "suitable_for": [
                "微服务架构",
                "云原生 / Kubernetes 部署",
                "需要高性能和高并发的服务",
                "DevOps 团队 (部署简单)"
            ],
            "not_suitable_for": [
                "复杂业务逻辑需要大量继承/泛型",
                "需要丰富 ORM 功能的场景"
            ],
            "complexity": "低",
            "performance": "高",
            "time_to_market": "快"
        },
        "python_fastapi": {
            "name": "Python + FastAPI",
            "framework": "FastAPI",
            "orm": "SQLAlchemy",
            "pros": [
                "Python 语法简洁，开发效率极高",
                "类型提示完善，IDE 支持好",
                "自动生成 OpenAPI 文档",
                "异步支持好 (async/await)",
                "AI/ML 集成最方便",
                "学习曲线最低"
            ],
            "cons": [
                "运行时错误，只有执行到才报错",
                "性能不如 Go/Rust/Java",
                "GIL 限制多线程性能",
                "类型提示容易被滥用导致运行时问题"
            ],
            "suitable_for": [
                "AI 相关应用 (LangChain, LLM 集成)",
                "快速原型和 MVP",
                "数据处理和 ETL",
                "小型到中型 Web 服务"
            ],
            "not_suitable_for": [
                "对性能要求极高的核心服务",
                "需要编译时检查的项目",
                "需要强类型保证的大型团队项目"
            ],
            "complexity": "低",
            "performance": "中",
            "time_to_market": "很快"
        }
    },
    "frontend": {
        "react_vite": {
            "name": "React + Vite",
            "ui_library": "可选 shadcn/ui 或 Ant Design",
            "pros": [
                "React 生态最丰富",
                "Vite 极速开发体验 (HMR)",
                "TypeScript 支持完善",
                "组件复用性高"
            ],
            "cons": [
                "React 18 之前版本状态管理较繁琐",
                "需要选择额外状态管理方案",
                "版本升级有时带来 breaking changes"
            ],
            "suitable_for": [
                "大多数 Web 应用场景",
                "需要高度定制的 UI",
                "大型单页应用"
            ],
            "not_suitable_for": [
                "追求极简的项目 (可考虑 Vue/Svelte)",
                "需要 Server-Side Rendering 的 SEO 敏感场景"
            ],
            "complexity": "中",
            "performance": "高",
            "time_to_market": "快"
        }
    },
    "database": {
        "postgresql": {
            "name": "PostgreSQL",
            "pros": [
                "功能最强大的开源关系型数据库",
                "JSON 支持 (JSONB)，兼顾关系和文档",
                "丰富的数据类型 (数组、全文搜索、GIS)",
                "性能优异，索引机制完善",
                "MVCC 支持，高并发表现好"
            ],
            "cons": [
                "对于简单查询比 MySQL 稍慢",
                "某些云服务商托管价格较高",
                "运维需要一定专业知识"
            ],
            "suitable_for": [
                "几乎所有业务场景",
                "需要复杂查询和事务",
                "需要 JSON 灵活存储"
            ],
            "not_suitable_for": [
                "超大规模简单 KV 场景 (用 Redis/Cassandra)",
                "完全无结构化数据 (用 MongoDB)"
            ]
        },
        "mysql": {
            "name": "MySQL",
            "pros": [
                "使用最广泛，文档社区极其丰富",
                "简单查询性能优异",
                "主从复制成熟稳定",
                "云服务商支持好，托管服务多"
            ],
            "cons": [
                "复杂查询性能不如 PostgreSQL",
                "JSON 支持不如 PostgreSQL",
                "事务隔离级别有限"
            ],
            "suitable_for": [
                "互联网产品 (微博、电商等)",
                "读多写少场景",
                "对 MySQL 运维熟悉的团队"
            ],
            "not_suitable_for": [
                "复杂事务场景",
                "需要 JSON 灵活存储"
            ]
        },
        "redis": {
            "name": "Redis",
            "pros": [
                "内存数据库，性能极高",
                "支持多种数据结构 (String/Hash/List/Set/SortedSet)",
                "丰富的数据持久化策略",
                "Pub/Sub、Pipeline、Lua 脚本等高级功能"
            ],
            "cons": [
                "内存容量限制数据量",
                "持久化机制有数据丢失风险",
                "单线程模型，复杂操作可能阻塞"
            ],
            "suitable_for": [
                "缓存层",
                "Session 存储",
                "实时排行榜、计数器",
                "消息队列"
            ],
            "not_suitable_for": [
                "主数据存储",
                "超大数据量存储"
            ]
        },
        "elasticsearch": {
            "name": "Elasticsearch",
            "pros": [
                "全文搜索能力最强",
                "分布式可扩展性好",
                "近实时搜索",
                "聚合分析功能强大"
            ],
            "cons": [
                "资源消耗大",
                "数据一致性不如主流通用数据库",
                "运维复杂度高"
            ],
            "suitable_for": [
                "全文搜索需求",
                "日志分析 (ELK Stack)",
                "数据分析仪表盘"
            ],
            "not_suitable_for": [
                "主数据存储",
                "简单 KV 存储"
            ]
        }
    },
    "deployment": {
        "kubernetes_helm": {
            "name": "Kubernetes + Helm",
            "pros": [
                "容器编排事实标准",
                "自动扩缩容、负载均衡",
                " Helm Chart 可复用地部署应用"
            ],
            "cons": [
                "学习曲线陡峭",
                "运维成本高",
                "资源开销大"
            ],
            "suitable_for": [
                "微服务架构",
                "需要高可用 / 自动恢复",
                "多环境部署"
            ],
            "not_suitable_for": [
                "单体应用简单部署",
                "资源受限的小团队"
            ]
        },
        "kubernetes_operator": {
            "name": "Kubernetes + Go Operator",
            "pros": [
                "Kubernetes 原生扩展",
                "CRD 定义领域模型",
                "自动化运维任务"
            ],
            "cons": [
                "开发 Operator 成本高",
                "需要 Go 语言能力",
                "复杂度最高"
            ],
            "suitable_for": [
                "复杂的有状态应用",
                "需要深度 Kubernetes 集成"
            ],
            "not_suitable_for": [
                "简单无状态服务"
            ]
        },
        "spring_cloud": {
            "name": "Spring Cloud",
            "pros": [
                "完整的微服务解决方案",
                "服务注册/发现、配置中心、网关等开箱即用",
                "与 Spring Boot 无缝集成"
            ],
            "cons": [
                "重量级，适合 Java 技术栈",
                "版本管理复杂",
                "资源消耗较大"
            ],
            "suitable_for": [
                "Spring Boot 微服务架构",
                "企业级微服务"
            ],
            "not_suitable_for": [
                "非 Java 技术栈",
                "轻量级服务"
            ]
        }
    },
    "cicd": {
        "github_actions": {
            "name": "GitHub Actions",
            "pros": [
                "与 GitHub 深度集成",
                "YAML 配置简单",
                "市场丰富 (actions Hub)",
                "免费额度充足"
            ],
            "cons": [
                "只能用于 GitHub",
                "自定义 runner 需要自托管"
            ],
            "suitable_for": [
                "GitHub 托管的项目",
                "开源项目"
            ],
            "not_suitable_for": [
                "非 GitHub 项目"
            ]
        },
        "jenkins": {
            "name": "Jenkins",
            "pros": [
                "最成熟的 CI/CD 工具",
                "插件生态极其丰富",
                "自托管，完全可控"
            ],
            "cons": [
                "配置复杂，界面老旧",
                "维护成本高",
                "Pipeline 脚本编写繁琐"
            ],
            "suitable_for": [
                "需要完全自托管",
                "复杂 CI/CD 流程",
                "旧有 Jenkins 基础设施"
            ],
            "not_suitable_for": [
                "追求简单快速的团队"
            ]
        }
    }
}


class TechStackRecommender:
    """技术栈推荐服务"""

    def __init__(self, prd_data: dict):
        """
        初始化推荐器

        Args:
            prd_data: Machine PRD 内容
        """
        self.prd = prd_data

    def analyze_requirements(self) -> dict:
        """分析需求特征"""
        features = self.prd.get("features", [])
        non_functional = self.prd.get("non_functional", {})
        integrations = self.prd.get("integrations", [])

        return {
            "scale": self._analyze_scale(features, non_functional),
            "team": self._analyze_team(non_functional),
            "performance": self._analyze_performance(non_functional),
            "time_pressure": self._analyze_time_pressure(non_functional),
            "has_ai_requirement": self._has_ai_requirement(features, integrations)
        }

    def _analyze_scale(self, features: list, non_functional: dict) -> str:
        """分析项目规模"""
        feature_count = len(features)
        expected_users = non_functional.get("expected_users", "unknown")

        if feature_count > 20 or expected_users == "large":
            return "large"
        elif feature_count > 5 or expected_users == "medium":
            return "medium"
        return "small"

    def _analyze_team(self, non_functional: dict) -> dict:
        """分析团队情况"""
        team_size = non_functional.get("team_size", "small")
        tech_familiarity = non_functional.get("tech_familiarity", "varied")
        return {"size": team_size, "tech_familiarity": tech_familiarity}

    def _analyze_performance(self, non_functional: dict) -> str:
        """分析性能要求"""
        perf_requirements = non_functional.get("performance", {})
        if perf_requirements.get("concurrent_users"):
            return "high"
        return "normal"

    def _analyze_time_pressure(self, non_functional: dict) -> str:
        """分析时间压力"""
        timeline = non_functional.get("timeline", "normal")
        if timeline in ["urgent", "very_urgent"]:
            return "high"
        elif timeline == "flexible":
            return "low"
        return "medium"

    def _has_ai_requirement(self, features: list, integrations: list) -> bool:
        """检查是否有 AI 需求"""
        ai_keywords = ["ai", "llm", "gpt", "chat", "nlp", "图像识别", "语音"]
        feature_text = " ".join(features).lower()
        integration_text = " ".join(integrations).lower()

        for keyword in ai_keywords:
            if keyword in feature_text or keyword in integration_text:
                return True
        return False

    def recommend(self) -> list:
        """
        推荐 1-3 套技术方案

        Returns:
            技术方案列表，每套方案包含推荐理由和权衡说明
        """
        analysis = self.analyze_requirements()
        recommendations = []

        # 根据分析结果生成推荐
        if analysis["has_ai_requirement"]:
            recommendations.append(self._recommend_python_fastapi(analysis))
        else:
            recommendations.append(self._recommend_go_gin(analysis))

        # 根据规模和时间压力调整
        if analysis["scale"] == "large" and analysis["time_pressure"] != "high":
            recommendations.append(self._recommend_java_spring(analysis))
        elif analysis["time_pressure"] == "high":
            recommendations.append(self._recommend_python_fastapi(analysis))

        # 如果推荐不足 3 个，补充 Java 方案
        if len(recommendations) < 3 and analysis["scale"] != "small":
            recommendations.append(self._recommend_java_quarkus(analysis))

        return recommendations[:3]

    def _recommend_python_fastapi(self, analysis: dict) -> dict:
        """推荐 Python FastAPI 方案"""
        return {
            "name": "快速原型方案",
            "description": "最适合快速交付和 AI 集成的方案",
            "backend": TECH_STACK_LIBRARY["backend"]["python_fastapi"],
            "frontend": TECH_STACK_LIBRARY["frontend"]["react_vite"],
            "database": TECH_STACK_LIBRARY["database"]["postgresql"],
            "cache": TECH_STACK_LIBRARY["database"]["redis"],
            "deployment": TECH_STACK_LIBRARY["deployment"]["kubernetes_helm"],
            "cicd": TECH_STACK_LIBRARY["cicd"]["github_actions"],
            "reason": self._build_reason("python_fastapi", analysis),
            "trade_offs": self._build_trade_offs("python_fastapi")
        }

    def _recommend_go_gin(self, analysis: dict) -> dict:
        """推荐 Go Gin 方案"""
        return {
            "name": "高性能微服务方案",
            "description": "平衡开发效率和运行性能的方案",
            "backend": TECH_STACK_LIBRARY["backend"]["go_gin"],
            "frontend": TECH_STACK_LIBRARY["frontend"]["react_vite"],
            "database": TECH_STACK_LIBRARY["database"]["postgresql"],
            "cache": TECH_STACK_LIBRARY["database"]["redis"],
            "deployment": TECH_STACK_LIBRARY["deployment"]["kubernetes_helm"],
            "cicd": TECH_STACK_LIBRARY["cicd"]["github_actions"],
            "reason": self._build_reason("go_gin", analysis),
            "trade_offs": self._build_trade_offs("go_gin")
        }

    def _recommend_java_spring(self, analysis: dict) -> dict:
        """推荐 Java Spring 方案"""
        return {
            "name": "企业级稳定方案",
            "description": "适合大型复杂业务系统的方案",
            "backend": TECH_STACK_LIBRARY["backend"]["java_spring"],
            "frontend": TECH_STACK_LIBRARY["frontend"]["react_vite"],
            "database": TECH_STACK_LIBRARY["database"]["postgresql"],
            "cache": TECH_STACK_LIBRARY["database"]["redis"],
            "deployment": TECH_STACK_LIBRARY["deployment"]["spring_cloud"],
            "cicd": TECH_STACK_LIBRARY["cicd"]["jenkins"],
            "reason": self._build_reason("java_spring", analysis),
            "trade_offs": self._build_trade_offs("java_spring")
        }

    def _recommend_java_quarkus(self, analysis: dict) -> dict:
        """推荐 Java Quarkus 方案"""
        return {
            "name": "云原生 Java 方案",
            "description": "现代化云原生 Java 开发体验",
            "backend": TECH_STACK_LIBRARY["backend"]["java_quarkus"],
            "frontend": TECH_STACK_LIBRARY["frontend"]["react_vite"],
            "database": TECH_STACK_LIBRARY["database"]["postgresql"],
            "cache": TECH_STACK_LIBRARY["database"]["redis"],
            "deployment": TECH_STACK_LIBRARY["deployment"]["kubernetes_helm"],
            "cicd": TECH_STACK_LIBRARY["cicd"]["github_actions"],
            "reason": self._build_reason("java_quarkus", analysis),
            "trade_offs": self._build_trade_offs("java_quarkus")
        }

    def _build_reason(self, backend_key: str, analysis: dict) -> str:
        """构建推荐理由"""
        reasons = []
        if backend_key == "python_fastapi":
            if analysis["has_ai_requirement"]:
                reasons.append("AI 集成需求强烈，Python 是 AI/ML 领域的首选语言")
            if analysis["time_pressure"] == "high":
                reasons.append("时间紧迫，需要快速交付")
            if analysis["scale"] == "small":
                reasons.append("小规模项目，FastAPI 可以快速完成开发")
        elif backend_key == "go_gin":
            if analysis["performance"] == "high":
                reasons.append("性能要求高，Go 语言性能优异")
            if analysis["time_pressure"] == "medium":
                reasons.append("Go 语言简洁，兼顾开发效率和运行性能")
            reasons.append("微服务友好，部署简单")
        elif backend_key == "java_spring":
            if analysis["scale"] == "large":
                reasons.append("大规模系统，企业级稳定性重要")
            reasons.append("Spring 生态最完善，社区支持好")
        elif backend_key == "java_quarkus":
            reasons.append("云原生部署，Quarkus 启动极快")
            reasons.append("内存占用低，适合容器化")
        return "；".join(reasons) if reasons else "综合评估后的推荐方案"

    def _build_trade_offs(self, backend_key: str) -> dict:
        """构建权衡说明"""
        info = TECH_STACK_LIBRARY["backend"][backend_key]
        return {
            "pros": info["pros"],
            "cons": info["cons"],
            "complexity": info["complexity"],
            "performance": info["performance"],
            "time_to_market": info["time_to_market"],
            "suitable_for": info["suitable_for"],
            "not_suitable_for": info["not_suitable_for"]
        }

    def get_library(self) -> dict:
        """获取完整的技术栈选项库"""
        return TECH_STACK_LIBRARY


class TechStackValidator:
    """技术栈验证服务"""

    def __init__(self, selected_stack: dict, prd_data: dict):
        """
        初始化验证器

        Args:
            selected_stack: 用户选择的技术栈
            prd_data: Machine PRD 内容
        """
        self.selected = selected_stack
        self.prd = prd_data

    def validate(self) -> dict:
        """
        验证技术栈选择的合理性

        Returns:
            验证报告，包含通过/警告状态和建议
        """
        warnings = []
        suggestions = []

        # 检查后端选择
        backend_warning = self._check_backend()
        if backend_warning:
            warnings.append(backend_warning)

        # 检查数据库选择
        db_warning = self._check_database()
        if db_warning:
            warnings.append(db_warning)

        # 检查部署方式
        deploy_warning = self._check_deployment()
        if deploy_warning:
            warnings.append(deploy_warning)

        # 检查 AI 需求
        if self._has_ai_requirement() and self._backend_is_not_python():
            suggestions.append({
                "type": "suggestion",
                "message": "检测到 AI 相关需求，建议考虑 Python 作为后端语言以获得更好的 AI 集成体验"
            })

        # 检查性能要求
        perf_warning = self._check_performance()
        if perf_warning:
            warnings.append(perf_warning)

        return {
            "status": "passed" if len(warnings) == 0 else "warning",
            "warnings": warnings,
            "suggestions": suggestions,
            "summary": self._build_summary(warnings, suggestions)
        }

    def _check_backend(self) -> Optional[dict]:
        """检查后端选择"""
        backend = self.selected.get("backend", {})
        backend_key = backend.get("key", "")

        # Rust + 快速原型 = 不合适
        if backend_key == "rust_actix":
            features = self.prd.get("features", [])
            if len(features) < 10:
                return {
                    "type": "warning",
                    "severity": "high",
                    "message": f"Rust ({backend.get('name')}) 学习曲线陡峭，编译时间长，不适合快速原型开发",
                    "suggestion": "如果团队没有 Rust 经验，建议选择 Go + Gin 或 Python + FastAPI"
                }

        # Python 用于大型高性能系统
        if backend_key == "python_fastapi":
            features = self.prd.get("features", [])
            non_functional = self.prd.get("non_functional", {})
            if len(features) > 30 or non_functional.get("expected_users") == "large":
                return {
                    "type": "warning",
                    "severity": "medium",
                    "message": "Python FastAPI 在超大规模系统中的性能可能不足",
                    "suggestion": "考虑使用 Go + Gin 或 Java Spring Boot 以获得更好的性能"
                }

        return None

    def _check_database(self) -> Optional[dict]:
        """检查数据库选择"""
        db = self.selected.get("database", {})
        db_key = db.get("key", "")

        features = self.prd.get("features", [])
        integrations = self.prd.get("integrations", [])

        # 简单项目用 Elasticsearch
        if db_key == "elasticsearch":
            if len(features) < 5 and not any("搜索" in f for f in features):
                return {
                    "type": "warning",
                    "severity": "low",
                    "message": "Elasticsearch 资源消耗大，运维复杂",
                    "suggestion": "如果搜索不是核心需求，可以先使用 PostgreSQL 的全文搜索功能"
                }

        return None

    def _check_deployment(self) -> Optional[dict]:
        """检查部署方式"""
        deploy = self.selected.get("deployment", {})
        deploy_key = deploy.get("key", "")
        features = self.prd.get("features", [])

        # 单体应用用 K8s
        if deploy_key in ["kubernetes_helm", "kubernetes_operator"]:
            if len(features) < 5:
                return {
                    "type": "warning",
                    "severity": "low",
                    "message": "Kubernetes 复杂度较高，对于简单项目可能过度设计",
                    "suggestion": "可以考虑简单的 Docker + Docker Compose 部署"
                }

        return None

    def _check_performance(self) -> Optional[dict]:
        """检查性能要求匹配"""
        backend = self.selected.get("backend", {})
        backend_key = backend.get("key", "")
        non_functional = self.prd.get("non_functional", {})
        perf_req = non_functional.get("performance", {})

        # 高并发要求但选择 Python
        if backend_key == "python_fastapi":
            if perf_req.get("concurrent_users") == "high" or perf_req.get("response_time") == "ms":
                return {
                    "type": "warning",
                    "severity": "high",
                    "message": "Python (GIL) 在高并发场景下性能受限",
                    "suggestion": "考虑使用 Go + Gin 或 Rust + Actix 以满足性能需求"
                }

        return None

    def _has_ai_requirement(self) -> bool:
        """检查是否有 AI 需求"""
        features = self.prd.get("features", [])
        integrations = self.prd.get("integrations", [])
        ai_keywords = ["ai", "llm", "gpt", "chat", "nlp", "图像识别", "语音"]
        text = " ".join(features + integrations).lower()
        return any(keyword in text for keyword in ai_keywords)

    def _backend_is_not_python(self) -> bool:
        """检查后端是否不是 Python"""
        backend = self.selected.get("backend", {})
        return backend.get("key") != "python_fastapi"

    def _build_summary(self, warnings: list, suggestions: list) -> str:
        """构建总结"""
        if len(warnings) == 0 and len(suggestions) == 0:
            return "技术栈选择合理，未发现明显问题"
        elif len(warnings) == 0:
            return f"技术栈选择基本合理，有 {len(suggestions)} 条建议"
        else:
            return f"发现 {len(warnings)} 个潜在问题，请仔细评估"
