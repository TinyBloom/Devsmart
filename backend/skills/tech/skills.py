from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from ..base import BaseSkill, LLMSkill
from ..models import Artifact, SkillCategory, SkillContext, SkillManifest, SkillResult


class AnalyzeTechnicalConstraintsInput(BaseModel):
    machine_prd: dict[str, Any]
    organization_constraints: dict[str, Any] = Field(default_factory=dict)


class TechnicalConstraint(BaseModel):
    id: str
    type: Literal["runtime", "scale", "security", "compliance", "integration", "team", "delivery", "cost"]
    description: str
    hard: bool = False
    evidence: str


class AnalyzeTechnicalConstraintsOutput(BaseModel):
    constraints: list[TechnicalConstraint]
    architectural_drivers: list[str]
    unknowns: list[str] = Field(default_factory=list)


class AnalyzeTechnicalConstraintsSkill(LLMSkill):
    manifest = SkillManifest(
        id="devsmart.tech.analyze-constraints", name="Analyze Technical Constraints", version="1.0.0",
        category=SkillCategory.ANALYZE, description="从 PRD 和组织约束提取技术决策驱动因素。",
        input_model=AnalyzeTechnicalConstraintsInput, output_model=AnalyzeTechnicalConstraintsOutput, tags=("tech", "architecture"),
    )

    @property
    def system_prompt(self) -> str:
        return """你是软件架构师。提取明确的硬约束、软约束和架构驱动因素。每项约束必须有证据；未知信息放入 unknowns，禁止把偏好伪装成硬约束。只输出符合 Schema 的 JSON。"""


class RecommendTechStackInput(BaseModel):
    machine_prd: dict[str, Any]
    analysis: AnalyzeTechnicalConstraintsOutput
    allowed_technologies: list[str] = Field(default_factory=list)


class TechnologyChoice(BaseModel):
    layer: str
    choice: str
    version_range: str | None = None
    rationale: str
    alternatives: list[str] = Field(default_factory=list)
    constraint_ids: list[str] = Field(default_factory=list)


class RecommendTechStackOutput(BaseModel):
    architecture_style: str
    choices: list[TechnologyChoice]
    risks: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class RecommendTechStackSkill(LLMSkill):
    manifest = SkillManifest(
        id="devsmart.tech.recommend-stack", name="Recommend Tech Stack", version="1.0.0",
        category=SkillCategory.GENERATE, description="基于约束生成可解释的技术栈建议。",
        input_model=RecommendTechStackInput, output_model=RecommendTechStackOutput, tags=("tech", "architecture"),
    )

    @property
    def system_prompt(self) -> str:
        return """根据机器 PRD 和技术约束选择最小充分技术栈。优先成熟、易维护方案，避免无依据微服务化。若 allowed_technologies 非空，只能从中选择。每项选择关联 constraint_ids，并列出替代方案、风险和假设。只输出符合 Schema 的 JSON。"""


class ValidateTechStackCompatibilityInput(BaseModel):
    recommendation: RecommendTechStackOutput
    prohibited_technologies: list[str] = Field(default_factory=list)
    required_layers: list[str] = Field(default_factory=lambda: ["frontend", "backend", "database"])


class CompatibilityIssue(BaseModel):
    code: str
    message: str
    severity: Literal["warning", "error"]


class ValidateTechStackCompatibilityOutput(BaseModel):
    valid: bool
    issues: list[CompatibilityIssue] = Field(default_factory=list)


class ValidateTechStackCompatibilitySkill(BaseSkill):
    manifest = SkillManifest(
        id="devsmart.tech.validate-compatibility", name="Validate Tech Stack Compatibility", version="1.0.0",
        category=SkillCategory.VALIDATE, description="确定性检查技术栈层级完整性、禁用项和重复项。",
        input_model=ValidateTechStackCompatibilityInput, output_model=ValidateTechStackCompatibilityOutput,
        tags=("tech", "validator"),
    )

    async def execute(self, context: SkillContext, skill_input: ValidateTechStackCompatibilityInput) -> SkillResult:
        issues: list[CompatibilityIssue] = []
        choices = skill_input.recommendation.choices
        layers = [c.layer.lower() for c in choices]
        for required in skill_input.required_layers:
            if required.lower() not in layers:
                issues.append(CompatibilityIssue(code="missing_layer", message=f"缺少技术层：{required}", severity="error"))
        prohibited = {x.lower() for x in skill_input.prohibited_technologies}
        for choice in choices:
            if choice.choice.lower() in prohibited:
                issues.append(CompatibilityIssue(code="prohibited_technology", message=f"使用了禁用技术：{choice.choice}", severity="error"))
        duplicates = {layer for layer in layers if layers.count(layer) > 1}
        for layer in sorted(duplicates):
            issues.append(CompatibilityIssue(code="duplicate_layer", message=f"同一层存在多个主选项：{layer}", severity="warning"))
        output = ValidateTechStackCompatibilityOutput(valid=not any(i.severity == "error" for i in issues), issues=issues)
        return SkillResult(output=output.model_dump(mode="json"))


class GenerateAdrInput(BaseModel):
    project_name: str
    recommendation: RecommendTechStackOutput
    constraints: AnalyzeTechnicalConstraintsOutput


class GenerateAdrOutput(BaseModel):
    title: str
    markdown: str
    status: Literal["proposed", "accepted"] = "proposed"


class GenerateArchitectureDecisionRecordSkill(LLMSkill):
    manifest = SkillManifest(
        id="devsmart.tech.generate-adr", name="Generate Architecture Decision Record", version="1.0.0",
        category=SkillCategory.GENERATE, description="将技术栈建议固化为可评审 ADR。",
        input_model=GenerateAdrInput, output_model=GenerateAdrOutput, tags=("tech", "adr"),
    )

    @property
    def system_prompt(self) -> str:
        return """生成一份 ADR Markdown，包含 Context、Decision、Decision Drivers、Considered Options、Consequences、Risks、Validation Plan。明确区分事实、约束与假设。JSON 中 markdown 字段承载完整文档。"""

    async def execute(self, context: SkillContext, skill_input: GenerateAdrInput) -> SkillResult:
        result = await super().execute(context, skill_input)
        result.artifacts.append(Artifact(type="adr", path="architecture/0001-tech-stack.md", content=result.output["markdown"], media_type="text/markdown"))
        return result
