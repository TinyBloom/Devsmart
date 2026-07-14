from __future__ import annotations

from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field

from .base import BaseSkill, LLMSkill
from .models import Artifact, SkillCategory, SkillContext, SkillManifest, SkillResult


class ArchitectureInput(BaseModel):
    project_name: str
    machine_prd: dict[str, Any]
    chosen_stack: dict[str, Any] = Field(default_factory=dict)


class ArchitectureOutput(BaseModel):
    architecture_version: str = "1.0"
    system: dict[str, Any]
    modules: list[dict[str, Any]]
    layers: list[dict[str, Any]]
    dependency_rules: list[dict[str, Any]]
    data_architecture: dict[str, Any]
    api_contract: dict[str, Any]
    security: dict[str, Any]
    observability: dict[str, Any]
    deployment: dict[str, Any]
    decisions: list[dict[str, Any]] = Field(default_factory=list)
    risks: list[dict[str, Any]] = Field(default_factory=list)
    open_questions: list[dict[str, Any]] = Field(default_factory=list)


class GenerateArchitectureSkill(LLMSkill):
    manifest = SkillManifest(
        id="devsmart.architecture.generate", name="Generate Architecture", version="1.0.0",
        category=SkillCategory.GENERATE, description="根据 Machine PRD 与技术栈生成可约束代码生成的架构契约。",
        input_model=ArchitectureInput, output_model=ArchitectureOutput, tags=("architecture", "codegen"),
    )

    @property
    def system_prompt(self) -> str:
        return """你是软件架构师。根据 Machine PRD 和 chosen_stack 输出机器可读 Architecture Contract。
必须：
- 优先模块化单体，除非需求明确需要分布式；按业务模块划分 ownership。
- 明确 API/Application/Domain/Infrastructure 或等价分层的职责与禁止行为。
- dependency_rules 必须可执行检查，包含 source、target、allowed、reason。
- data_architecture 明确实体关系、事务边界、删除策略、历史快照策略、迁移与数据库可移植规则。
- api_contract 明确 OpenAPI 是否为单一契约源、DTO 生成策略、命名与版本策略。
- security 明确认证、授权、密钥、密码、输入验证和敏感字段规则。
- observability 明确结构化日志、request_id、指标和健康检查。
- deployment 明确运行单元、环境变量、容器、迁移与回滚策略。
- decisions 使用稳定 ADR ID，记录背景、决策、理由、后果和状态。
- 不得自行改变 Machine PRD；冲突或关键未知项放入 open_questions，标注 blocking。
只输出符合 Schema 的 JSON。"""

    async def execute(self, context: SkillContext, skill_input: ArchitectureInput) -> SkillResult:
        result = await super().execute(context, skill_input)
        result.artifacts.append(Artifact(type="architecture", path="architecture/architecture.yaml", content=yaml.safe_dump(result.output, allow_unicode=True, sort_keys=False), media_type="application/yaml"))
        return result


class ArchitectureIssue(BaseModel):
    code: str
    message: str
    severity: Literal["warning", "error"]
    reference_id: str | None = None


class ValidateArchitectureInput(BaseModel):
    architecture: ArchitectureOutput


class ValidateArchitectureOutput(BaseModel):
    valid: bool
    issues: list[ArchitectureIssue] = Field(default_factory=list)


class ValidateArchitectureSkill(BaseSkill):
    manifest = SkillManifest(
        id="devsmart.architecture.validate", name="Validate Architecture", version="1.0.0",
        category=SkillCategory.VALIDATE, description="确定性检查架构契约是否足以约束代码生成。",
        input_model=ValidateArchitectureInput, output_model=ValidateArchitectureOutput, tags=("architecture", "validator"),
    )

    async def execute(self, context: SkillContext, skill_input: ValidateArchitectureInput) -> SkillResult:
        a = skill_input.architecture
        issues: list[ArchitectureIssue] = []
        for field_name, value in (("modules", a.modules), ("layers", a.layers), ("dependency_rules", a.dependency_rules)):
            if not value:
                issues.append(ArchitectureIssue(code=f"missing_{field_name}", message=f"缺少 {field_name}", severity="error"))
        module_ids = [str(x.get("id") or x.get("name")) for x in a.modules]
        if len(module_ids) != len(set(module_ids)):
            issues.append(ArchitectureIssue(code="duplicate_module", message="模块 ID 或名称重复", severity="error"))
        for key, value in (("data_architecture", a.data_architecture), ("api_contract", a.api_contract), ("security", a.security), ("deployment", a.deployment)):
            if not value:
                issues.append(ArchitectureIssue(code=f"missing_{key}", message=f"缺少 {key}", severity="error"))
        if any(bool(q.get("blocking")) for q in a.open_questions):
            issues.append(ArchitectureIssue(code="blocking_open_question", message="架构仍存在阻塞性开放问题", severity="error"))
        output = ValidateArchitectureOutput(valid=not any(i.severity == "error" for i in issues), issues=issues)
        return SkillResult(output=output.model_dump(mode="json"))
