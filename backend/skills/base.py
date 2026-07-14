from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

from .errors import SkillExecutionError
from .models import SkillContext, SkillManifest, SkillMetrics, SkillResult


class BaseSkill(ABC):
    manifest: SkillManifest

    @abstractmethod
    async def execute(self, context: SkillContext, skill_input: BaseModel) -> SkillResult:
        raise NotImplementedError


class LLMSkill(BaseSkill):
    temperature = 0.2

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        raise NotImplementedError

    def build_user_prompt(self, skill_input: BaseModel) -> str:
        return json.dumps(skill_input.model_dump(mode="json"), ensure_ascii=False, indent=2)

    async def execute(self, context: SkillContext, skill_input: BaseModel) -> SkillResult:
        if context.llm is None:
            raise SkillExecutionError(f"{self.manifest.id} requires an LLM gateway")
        response = await context.llm.generate_json(
            system_prompt=self.system_prompt,
            user_prompt=self.build_user_prompt(skill_input),
            output_schema=self.manifest.output_model.model_json_schema(),
            temperature=self.temperature,
        )
        output = self.manifest.output_model.model_validate(response.data).model_dump(mode="json")
        return SkillResult(
            output=output,
            metrics=SkillMetrics(
                prompt_tokens=response.prompt_tokens,
                completion_tokens=response.completion_tokens,
                model=response.model,
            ),
        )
