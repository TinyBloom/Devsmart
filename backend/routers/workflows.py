from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from skills.catalog import build_default_registry
from skills.models import SkillContext
from skills.runner import SkillRunner
from workflows import WorkflowEngine

router = APIRouter(prefix="/api/workflows", tags=["workflows"])

runner = SkillRunner(build_default_registry())
workflow_engine = WorkflowEngine(runner, workflows_dir="workflows")
workflow_engine.load_workflows()


@router.get("/", response_model=List[Dict[str, Any]])
async def list_workflows():
    return workflow_engine.list_workflows()


@router.get("/{workflow_id}", response_model=Dict[str, Any])
async def get_workflow(workflow_id: str):
    workflow = workflow_engine.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
    return {
        "id": workflow.id,
        "version": workflow.version,
        "steps": [
            {
                "id": step.id,
                "uses": step.uses,
                "when": step.when,
            }
            for step in workflow.steps
        ],
    }


@router.post("/{workflow_id}/execute", response_model=Dict[str, Any])
async def execute_workflow(
    workflow_id: str,
    inputs: Dict[str, Any],
    project_id: str = "default",
):
    try:
        context = SkillContext(project_id=project_id)
        result = await workflow_engine.execute(workflow_id, inputs, context)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))