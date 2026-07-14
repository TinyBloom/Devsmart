import pytest

from backend.skills import SkillContext, SkillRunner, build_default_registry
from backend.skills.models import LLMResponse


class FakeLLM:
    def __init__(self, responses):
        self.responses = iter(responses)

    async def generate_json(self, **kwargs):
        return LLMResponse(data=next(self.responses), model="fake")


def test_registry_contains_enhanced_skills():
    registry = build_default_registry()
    ids = {skill.manifest.id for skill in registry.list()}
    assert len(ids) == 18
    assert {
        "devsmart.architecture.generate",
        "devsmart.architecture.validate",
        "devsmart.codegen.plan",
        "devsmart.codegen.validate-plan",
        "devsmart.feedback.diagnose",
        "devsmart.feedback.repair",
    } <= ids


@pytest.mark.asyncio
async def test_requirement_readiness_is_deterministic():
    runner = SkillRunner(build_default_registry())
    result = await runner.run(
        "devsmart.requirement.validate-readiness",
        {
            "requirements": {
                "goal": "减少团队报销处理时间",
                "target_users": ["员工", "财务"],
                "core_features": ["提交报销", "审批"],
                "acceptance_criteria": ["员工可以提交报销单"],
            }
        },
        SkillContext(project_id="demo"),
    )
    assert result.output["ready"] is True
    assert result.output["score"] == 100


@pytest.mark.asyncio
async def test_machine_prd_creates_yaml_artifact():
    fake = FakeLLM([{
        "schema_version": "1.0",
        "product": {"id": "expense", "name": "Expense"},
        "actors": [{"id": "ACT-EMPLOYEE", "name": "员工"}],
        "features": [{"id": "FEAT-SUBMIT", "name": "提交报销"}],
        "acceptance_criteria": [{"id": "AC-SUBMIT-001", "feature_id": "FEAT-SUBMIT", "statement": "可以提交"}],
    }])
    runner = SkillRunner(build_default_registry())
    result = await runner.run(
        "devsmart.prd.generate-machine",
        {"project_name": "Expense", "human_prd": "# PRD", "requirements": {}},
        SkillContext(project_id="demo", llm=fake),
    )
    assert result.artifacts[0].path == "prd/machine-prd.yaml"
    assert "FEAT-SUBMIT" in result.artifacts[0].content


@pytest.mark.asyncio
async def test_consistency_detects_uncovered_feature_and_unknown_error():
    runner = SkillRunner(build_default_registry())
    result = await runner.run(
        "devsmart.prd.validate-consistency",
        {
            "human_prd": "# PRD",
            "machine_prd": {
                "product": {"id": "x"},
                "features": [{"id": "FEAT-1"}],
                "api_contracts": [{
                    "id": "API-1", "method": "POST", "path": "/items",
                    "responses": {"400": {"error_codes": ["NOT_DEFINED"]}},
                }],
                "acceptance_criteria": [],
            },
        },
        SkillContext(project_id="demo"),
    )
    assert result.output["valid"] is False
    codes = {item["code"] for item in result.output["issues"]}
    assert "feature_without_acceptance" in codes
    assert "unknown_error_code" in codes


@pytest.mark.asyncio
async def test_architecture_validator_blocks_missing_contracts():
    runner = SkillRunner(build_default_registry())
    result = await runner.run(
        "devsmart.architecture.validate",
        {"architecture": {
            "system": {"style": "modular_monolith"},
            "modules": [], "layers": [], "dependency_rules": [],
            "data_architecture": {}, "api_contract": {}, "security": {},
            "observability": {}, "deployment": {},
        }},
        SkillContext(project_id="demo"),
    )
    assert result.output["valid"] is False
    assert len(result.output["issues"]) >= 7


@pytest.mark.asyncio
async def test_code_plan_validator_detects_cycle_and_coverage_gap():
    runner = SkillRunner(build_default_registry())
    task = lambda i, dep, req: {
        "id": i, "title": i, "phase": "backend", "depends_on": dep,
        "requirement_ids": req, "read_context": [],
        "write_scope": [f"backend/{i}/**"], "forbidden_scope": ["prd/**", "architecture/**"],
        "outputs": [f"backend/{i}/mod.py"], "validation_commands": ["pytest"],
        "definition_of_done": ["tests pass"],
    }
    result = await runner.run(
        "devsmart.codegen.validate-plan",
        {"plan": {
            "strategy": "incremental",
            "tasks": [task("TASK-A", ["TASK-B"], ["FEAT-1"]), task("TASK-B", ["TASK-A"], [])],
            "global_validation_commands": ["pytest"],
        }, "required_requirement_ids": ["FEAT-1", "BR-1"]},
        SkillContext(project_id="demo"),
    )
    assert result.output["valid"] is False
    codes = {item["code"] for item in result.output["issues"]}
    assert "cyclic_dependency" in codes
    assert result.output["uncovered_requirement_ids"] == ["BR-1"]
