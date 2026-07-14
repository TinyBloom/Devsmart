from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from skills.models import SkillContext, SkillResult
from skills.runner import SkillRunner
from skills.registry import SkillRegistry


class WorkflowStep:
    id: str
    uses: str
    when: Optional[str] = None
    with_: Optional[Dict[str, str]] = None


class WorkflowDefinition:
    id: str
    version: str
    steps: List[WorkflowStep]


class WorkflowEngine:
    def __init__(self, skill_runner: SkillRunner, workflows_dir: str = "workflows"):
        self.skill_runner = skill_runner
        self.workflows_dir = Path(workflows_dir)
        self._workflows: Dict[str, WorkflowDefinition] = {}

    def load_workflows(self) -> None:
        if not self.workflows_dir.exists():
            return
        for yaml_file in self.workflows_dir.glob("*.yaml"):
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            workflow = WorkflowDefinition()
            workflow.id = data.get("id")
            workflow.version = data.get("version", "1.0.0")
            workflow.steps = []
            for step_data in data.get("steps", []):
                step = WorkflowStep()
                step.id = step_data.get("id")
                step.uses = step_data.get("uses")
                step.when = step_data.get("when")
                step.with_ = step_data.get("with")
                workflow.steps.append(step)
            self._workflows[workflow.id] = workflow

    def list_workflows(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": w.id,
                "version": w.version,
                "steps": len(w.steps),
            }
            for w in self._workflows.values()
        ]

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        return self._workflows.get(workflow_id)

    async def execute(
        self,
        workflow_id: str,
        inputs: Dict[str, Any],
        context: SkillContext,
    ) -> Dict[str, Any]:
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        steps_output: Dict[str, Any] = {}
        artifacts: List[Dict[str, Any]] = []
        all_metrics: List[Dict[str, Any]] = []

        for step in workflow.steps:
            if step.when:
                if not self._evaluate_condition(step.when, steps_output, inputs):
                    continue

            skill_id, version = self._parse_uses(step.uses)

            step_inputs = self._build_step_inputs(step, inputs, steps_output)

            try:
                result: SkillResult = await self.skill_runner.run(
                    skill_id=skill_id,
                    payload=step_inputs,
                    context=context,
                    version=version,
                )

                steps_output[step.id] = result.output

                if result.artifacts:
                    artifacts.extend(
                        {
                            "type": art.type,
                            "path": art.path,
                            "content": art.content,
                        }
                        for art in result.artifacts
                    )

                if result.metrics:
                    all_metrics.append(
                        {
                            "step": step.id,
                            "duration_ms": result.metrics.duration_ms,
                            "prompt_tokens": result.metrics.prompt_tokens,
                            "completion_tokens": result.metrics.completion_tokens,
                            "model": result.metrics.model,
                        }
                    )

            except Exception as e:
                steps_output[step.id] = {"error": str(e)}

        return {
            "workflow_id": workflow.id,
            "version": workflow.version,
            "steps": steps_output,
            "artifacts": artifacts,
            "metrics": all_metrics,
        }

    def _evaluate_condition(self, condition: str, steps_output: Dict[str, Any], inputs: Dict[str, Any]) -> bool:
        try:
            context = {"steps": {"output": steps_output}, "inputs": inputs}
            return bool(eval(condition, {}, context))
        except Exception:
            return True

    def _parse_uses(self, uses: str) -> tuple[str, Optional[str]]:
        if "@" in uses:
            skill_id, version = uses.split("@", 1)
            return skill_id, version
        return uses, None

    def _build_step_inputs(self, step: WorkflowStep, inputs: Dict[str, Any], steps_output: Dict[str, Any]) -> Dict[str, Any]:
        step_inputs = inputs.copy()

        if step.with_:
            for key, value in step.with_.items():
                if isinstance(value, str) and value.startswith("steps."):
                    parts = value[6:].split(".")
                    data = steps_output
                    for part in parts:
                        if part in data:
                            data = data[part]
                        else:
                            data = None
                            break
                    step_inputs[key] = data
                elif isinstance(value, str) and value.startswith("inputs."):
                    step_inputs[key] = inputs.get(value[7:])
                else:
                    step_inputs[key] = value

        for step_id, output in steps_output.items():
            step_inputs[f"steps.{step_id}"] = output

        return step_inputs