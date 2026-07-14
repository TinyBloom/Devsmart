from __future__ import annotations

import asyncio
import time
from typing import Any

from pydantic import ValidationError

from .errors import SkillExecutionError, SkillValidationError
from .models import SkillContext, SkillResult, SkillStatus
from .registry import SkillRegistry


class SkillRunner:
    def __init__(self, registry: SkillRegistry) -> None:
        self.registry = registry

    async def run(
        self,
        skill_id: str,
        payload: dict[str, Any],
        context: SkillContext,
        version: str | None = None,
    ) -> SkillResult:
        skill = self.registry.get(skill_id, version)
        try:
            validated_input = skill.manifest.input_model.model_validate(payload)
        except ValidationError as exc:
            raise SkillValidationError(str(exc)) from exc

        started = time.perf_counter()
        last_error: Exception | None = None
        for attempt in range(1, skill.manifest.max_attempts + 1):
            try:
                result = await asyncio.wait_for(
                    skill.execute(context, validated_input),
                    timeout=skill.manifest.timeout_seconds,
                )
                skill.manifest.output_model.model_validate(result.output)
                result.metrics.duration_ms = int((time.perf_counter() - started) * 1000)
                return result
            except (ValidationError, ValueError, TimeoutError) as exc:
                last_error = exc
                if attempt == skill.manifest.max_attempts:
                    break

        return SkillResult(
            status=SkillStatus.FAILED,
            output={},
            warnings=[str(last_error or "Unknown skill error")],
        )
