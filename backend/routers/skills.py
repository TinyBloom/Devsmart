from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from skills.catalog import build_default_registry
from skills.models import SkillContext, SkillResult
from skills.runner import SkillRunner

router = APIRouter(prefix="/api/skills", tags=["skills"])

runner = SkillRunner(build_default_registry())


@router.get("/", response_model=List[Dict[str, Any]])
async def list_skills():
    skills = runner.registry.list()
    return [
        {
            "id": skill.manifest.id,
            "name": skill.manifest.name,
            "version": skill.manifest.version,
            "category": skill.manifest.category.value,
            "description": skill.manifest.description,
            "tags": list(skill.manifest.tags),
        }
        for skill in skills
    ]


@router.get("/{skill_id}", response_model=Dict[str, Any])
async def get_skill(skill_id: str, version: str = None):
    try:
        skill = runner.registry.get(skill_id, version)
        return {
            "id": skill.manifest.id,
            "name": skill.manifest.name,
            "version": skill.manifest.version,
            "category": skill.manifest.category.value,
            "description": skill.manifest.description,
            "input_model": skill.manifest.input_model.__name__,
            "output_model": skill.manifest.output_model.__name__,
            "timeout_seconds": skill.manifest.timeout_seconds,
            "max_attempts": skill.manifest.max_attempts,
            "tags": list(skill.manifest.tags),
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{skill_id}/execute", response_model=Dict[str, Any])
async def execute_skill(
    skill_id: str,
    payload: Dict[str, Any],
    project_id: str = "default",
    version: str = None,
):
    try:
        context = SkillContext(project_id=project_id)
        result: SkillResult = await runner.run(
            skill_id=skill_id,
            payload=payload,
            context=context,
            version=version,
        )
        return {
            "status": result.status.value,
            "output": result.output,
            "artifacts": [
                {
                    "type": art.type,
                    "path": art.path,
                    "media_type": art.media_type,
                }
                for art in result.artifacts
            ],
            "warnings": result.warnings,
            "metrics": {
                "duration_ms": result.metrics.duration_ms,
                "prompt_tokens": result.metrics.prompt_tokens,
                "completion_tokens": result.metrics.completion_tokens,
                "model": result.metrics.model,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))