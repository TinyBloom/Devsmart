from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field


class SkillCategory(str, Enum):
    ANALYZE = "analyze"
    GENERATE = "generate"
    VALIDATE = "validate"
    TRANSFORM = "transform"


class SkillStatus(str, Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class Artifact(BaseModel):
    type: str
    path: str
    content: str
    media_type: str = "text/plain"
    metadata: dict[str, Any] = Field(default_factory=dict)


class SkillMetrics(BaseModel):
    duration_ms: int = 0
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    model: str | None = None


class SkillResult(BaseModel):
    status: SkillStatus = SkillStatus.SUCCEEDED
    output: dict[str, Any] = Field(default_factory=dict)
    artifacts: list[Artifact] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metrics: SkillMetrics = Field(default_factory=SkillMetrics)


class SkillManifest(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    version: str
    category: SkillCategory
    description: str
    input_model: type[BaseModel]
    output_model: type[BaseModel]
    timeout_seconds: int = 120
    max_attempts: int = 1
    tags: tuple[str, ...] = ()


class LLMResponse(BaseModel):
    data: dict[str, Any]
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    model: str | None = None


class LLMGateway(Protocol):
    async def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        output_schema: dict[str, Any],
        temperature: float = 0.2,
    ) -> LLMResponse:
        ...


@dataclass(slots=True)
class SkillContext:
    project_id: str
    llm: LLMGateway | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class Skill(Protocol):
    manifest: SkillManifest

    async def execute(self, context: SkillContext, skill_input: BaseModel) -> SkillResult:
        ...
