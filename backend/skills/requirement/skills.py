from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from ..base import BaseSkill, LLMSkill
from ..models import SkillCategory, SkillContext, SkillManifest, SkillResult


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class RequirementDimension(BaseModel):
    name: str
    status: Literal["missing", "partial", "complete"]
    reason: str
    priority: Literal["low", "medium", "high"] = "medium"


class AnalyzeRequirementGapsInput(BaseModel):
    idea: str
    conversation: list[ConversationMessage] = Field(default_factory=list)
    requirements: dict[str, Any] = Field(default_factory=dict)


class AnalyzeRequirementGapsOutput(BaseModel):
    dimensions: list[RequirementDimension]
    completeness: int = Field(ge=0, le=100)
    summary: str


class AnalyzeRequirementGapsSkill(LLMSkill):
    manifest = SkillManifest(
        id="devsmart.requirement.analyze-gaps", name="Analyze Requirement Gaps", version="1.0.0",
        category=SkillCategory.ANALYZE, description="识别需求缺口并计算可解释的完整度。",
        input_model=AnalyzeRequirementGapsInput, output_model=AnalyzeRequirementGapsOutput, tags=("requirement",),
    )

    @property
    def system_prompt(self) -> str:
        return """你是软件需求分析师。分析产品想法、对话和已有结构化需求。按目标用户、核心场景、功能、数据、业务规则、非功能要求、集成、验收标准八个维度判断 missing/partial/complete。完整度必须与维度状态一致，不因无关维度缺失机械扣分。只输出符合 Schema 的 JSON。"""


class GenerateNextQuestionInput(BaseModel):
    gap_analysis: AnalyzeRequirementGapsOutput
    conversation: list[ConversationMessage] = Field(default_factory=list)


class GenerateNextQuestionOutput(BaseModel):
    question: str
    target_dimension: str
    rationale: str
    answer_format_hint: str | None = None


class GenerateNextQuestionSkill(LLMSkill):
    manifest = SkillManifest(
        id="devsmart.requirement.generate-next-question", name="Generate Next Requirement Question", version="1.0.0",
        category=SkillCategory.GENERATE, description="针对最高优先级需求缺口生成一个问题。",
        input_model=GenerateNextQuestionInput, output_model=GenerateNextQuestionOutput, tags=("requirement", "conversation"),
    )

    @property
    def system_prompt(self) -> str:
        return """你是需求访谈助手。一次只提出一个信息增益最高的问题，避免重复已问内容。问题应具体、易回答，优先阻塞产品范围或验收标准的缺口。只输出符合 Schema 的 JSON。"""


class UpdateStructuredRequirementsInput(BaseModel):
    current_requirements: dict[str, Any] = Field(default_factory=dict)
    latest_user_message: str
    question_dimension: str | None = None


class RequirementChange(BaseModel):
    path: str
    operation: Literal["set", "append", "remove"]
    value: Any = None
    evidence: str


class UpdateStructuredRequirementsOutput(BaseModel):
    requirements: dict[str, Any]
    changes: list[RequirementChange]
    unresolved_ambiguities: list[str] = Field(default_factory=list)


class UpdateStructuredRequirementsSkill(LLMSkill):
    manifest = SkillManifest(
        id="devsmart.requirement.update-structured", name="Update Structured Requirements", version="1.0.0",
        category=SkillCategory.TRANSFORM, description="将用户回答合并到结构化需求，并记录证据。",
        input_model=UpdateStructuredRequirementsInput, output_model=UpdateStructuredRequirementsOutput, tags=("requirement", "state"),
    )

    @property
    def system_prompt(self) -> str:
        return """把用户最新回答合并到结构化需求。禁止凭空补充事实；推断必须放入 unresolved_ambiguities。changes 使用点路径，evidence 引用用户表达的短摘要。只输出符合 Schema 的 JSON。"""


class ValidateRequirementReadinessInput(BaseModel):
    requirements: dict[str, Any]
    minimum_score: int = Field(default=75, ge=0, le=100)


class ReadinessIssue(BaseModel):
    code: str
    message: str
    severity: Literal["warning", "error"]


class ValidateRequirementReadinessOutput(BaseModel):
    ready: bool
    score: int = Field(ge=0, le=100)
    issues: list[ReadinessIssue] = Field(default_factory=list)


class ValidateRequirementReadinessSkill(BaseSkill):
    manifest = SkillManifest(
        id="devsmart.requirement.validate-readiness", name="Validate Requirement Readiness", version="1.0.0",
        category=SkillCategory.VALIDATE, description="使用确定性规则判断需求是否足以进入 PRD 生成。",
        input_model=ValidateRequirementReadinessInput, output_model=ValidateRequirementReadinessOutput,
        tags=("requirement", "validator"),
    )

    async def execute(self, context: SkillContext, skill_input: ValidateRequirementReadinessInput) -> SkillResult:
        req = skill_input.requirements
        checks = {
            "goal": bool(req.get("goal") or req.get("product_goal")),
            "users": bool(req.get("users") or req.get("target_users")),
            "features": bool(req.get("features") or req.get("core_features")),
            "acceptance": bool(req.get("acceptance_criteria")),
        }
        weights = {"goal": 25, "users": 20, "features": 35, "acceptance": 20}
        score = sum(weights[key] for key, passed in checks.items() if passed)
        issues = [
            ReadinessIssue(code=f"missing_{key}", message=f"缺少必要需求字段：{key}", severity="error")
            for key, passed in checks.items() if not passed
        ]
        output = ValidateRequirementReadinessOutput(
            ready=score >= skill_input.minimum_score and not any(i.code in {"missing_goal", "missing_features"} for i in issues),
            score=score,
            issues=issues,
        )
        return SkillResult(output=output.model_dump(mode="json"))
