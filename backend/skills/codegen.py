from __future__ import annotations

from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field

from .base import BaseSkill, LLMSkill
from .models import Artifact, SkillCategory, SkillContext, SkillManifest, SkillResult


class CodeTask(BaseModel):
    id: str
    title: str
    phase: Literal["scaffold", "database", "backend", "contract", "frontend", "tests", "deployment"]
    depends_on: list[str] = Field(default_factory=list)
    requirement_ids: list[str] = Field(default_factory=list)
    read_context: list[str] = Field(default_factory=list)
    write_scope: list[str]
    forbidden_scope: list[str] = Field(default_factory=list)
    outputs: list[str]
    validation_commands: list[str]
    definition_of_done: list[str]


class CodePlanInput(BaseModel):
    project_name: str
    machine_prd: dict[str, Any]
    architecture: dict[str, Any]
    chosen_stack: dict[str, Any] = Field(default_factory=dict)


class CodePlanOutput(BaseModel):
    plan_version: str = "1.0"
    strategy: str
    tasks: list[CodeTask]
    requirement_coverage: dict[str, list[str]] = Field(default_factory=dict)
    global_validation_commands: list[str]


class GenerateCodePlanSkill(LLMSkill):
    manifest = SkillManifest(
        id="devsmart.codegen.plan", name="Generate Code Plan", version="1.0.0",
        category=SkillCategory.GENERATE, description="将需求和架构拆成可验证、限制写入范围的代码生成任务 DAG。",
        input_model=CodePlanInput, output_model=CodePlanOutput, tags=("codegen", "planner"),
    )

    @property
    def system_prompt(self) -> str:
        return """你是代码生成规划器。不要输出代码；输出任务 DAG。
要求：
- 顺序覆盖 scaffold、database、backend shared、逐业务模块、OpenAPI/contract、frontend、tests、deployment。
- 每项任务使用稳定 TASK-* ID，depends_on 不得循环。
- requirement_ids 必须引用 Machine PRD 中存在的稳定 ID，并覆盖所有 P0/核心功能、业务规则、API 和验收标准。
- write_scope 必须最小化，禁止使用 **、项目根目录或空范围；forbidden_scope 必须保护 prd/** 和 architecture/**。
- outputs 必须为具体文件或窄目录；每项任务必须有可执行 validation_commands 和 definition_of_done。
- 共享契约先生成，前后端不得各自猜测 API 类型。
- 生成任务按模块切分，避免多个并行任务写同一文件。
- global_validation_commands 包含格式化、编译/类型检查、lint、单元、集成、构建和端到端测试（按技术栈选择）。
只输出符合 Schema 的 JSON。"""

    async def execute(self, context: SkillContext, skill_input: CodePlanInput) -> SkillResult:
        result = await super().execute(context, skill_input)
        result.artifacts.append(Artifact(type="generation_plan", path="generation/generation-plan.yaml", content=yaml.safe_dump(result.output, allow_unicode=True, sort_keys=False), media_type="application/yaml"))
        return result


class PlanIssue(BaseModel):
    code: str
    message: str
    severity: Literal["warning", "error"]
    reference_id: str | None = None


class ValidateCodePlanInput(BaseModel):
    plan: CodePlanOutput
    required_requirement_ids: list[str] = Field(default_factory=list)


class ValidateCodePlanOutput(BaseModel):
    valid: bool
    issues: list[PlanIssue] = Field(default_factory=list)
    uncovered_requirement_ids: list[str] = Field(default_factory=list)


class ValidateCodePlanSkill(BaseSkill):
    manifest = SkillManifest(
        id="devsmart.codegen.validate-plan", name="Validate Code Plan", version="1.0.0",
        category=SkillCategory.VALIDATE, description="检查任务 DAG、写入边界和需求覆盖。",
        input_model=ValidateCodePlanInput, output_model=ValidateCodePlanOutput, tags=("codegen", "validator"),
    )

    async def execute(self, context: SkillContext, skill_input: ValidateCodePlanInput) -> SkillResult:
        issues: list[PlanIssue] = []
        task_ids = [t.id for t in skill_input.plan.tasks]
        known = set(task_ids)
        if len(task_ids) != len(known):
            issues.append(PlanIssue(code="duplicate_task_id", message="任务 ID 重复", severity="error"))
        covered: set[str] = set()
        for task in skill_input.plan.tasks:
            covered.update(task.requirement_ids)
            unknown = set(task.depends_on) - known
            if unknown:
                issues.append(PlanIssue(code="unknown_dependency", message=f"任务 {task.id} 引用未知依赖：{sorted(unknown)}", severity="error", reference_id=task.id))
            if task.id in task.depends_on:
                issues.append(PlanIssue(code="self_dependency", message=f"任务 {task.id} 依赖自身", severity="error", reference_id=task.id))
            if not task.write_scope or any(x.strip() in {"", "**", "*", "/"} for x in task.write_scope):
                issues.append(PlanIssue(code="unsafe_write_scope", message=f"任务 {task.id} 写入范围过宽或为空", severity="error", reference_id=task.id))
            if not task.outputs or not task.validation_commands or not task.definition_of_done:
                issues.append(PlanIssue(code="incomplete_task", message=f"任务 {task.id} 缺少输出、验证命令或完成标准", severity="error", reference_id=task.id))
        # deterministic cycle check
        graph = {t.id: t.depends_on for t in skill_input.plan.tasks}
        visiting: set[str] = set(); visited: set[str] = set()
        def dfs(node: str) -> bool:
            if node in visiting: return True
            if node in visited: return False
            visiting.add(node)
            if any(dep in graph and dfs(dep) for dep in graph[node]): return True
            visiting.remove(node); visited.add(node); return False
        if any(dfs(node) for node in graph):
            issues.append(PlanIssue(code="cyclic_dependency", message="任务依赖存在循环", severity="error"))
        uncovered = sorted(set(skill_input.required_requirement_ids) - covered)
        if uncovered:
            issues.append(PlanIssue(code="uncovered_requirements", message=f"未覆盖需求：{uncovered}", severity="error"))
        output = ValidateCodePlanOutput(valid=not any(i.severity == "error" for i in issues), issues=issues, uncovered_requirement_ids=uncovered)
        return SkillResult(output=output.model_dump(mode="json"))


class DiagnoseInput(BaseModel):
    task_id: str
    command: str
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    allowed_files: list[str] = Field(default_factory=list)
    requirement_ids: list[str] = Field(default_factory=list)


class DiagnoseOutput(BaseModel):
    stage: str
    category: Literal["syntax_error", "type_error", "lint_error", "missing_dependency", "migration_error", "assertion_failure", "environment_error", "timeout", "unknown"]
    summary: str
    primary_error: dict[str, Any] = Field(default_factory=dict)
    suspected_files: list[str] = Field(default_factory=list)
    requirement_ids: list[str] = Field(default_factory=list)
    repair_strategy: str
    retry_safe: bool


class DiagnoseFailureSkill(LLMSkill):
    manifest = SkillManifest(
        id="devsmart.feedback.diagnose", name="Diagnose Build Failure", version="1.0.0",
        category=SkillCategory.ANALYZE, description="将编译、lint 和测试日志归一化为最小诊断包。",
        input_model=DiagnoseInput, output_model=DiagnoseOutput, tags=("feedback", "diagnose"),
    )
    temperature = 0.0

    @property
    def system_prompt(self) -> str:
        return """分析命令失败，输出结构化诊断。区分代码错误、依赖/迁移错误、环境错误和超时。
只引用日志中存在的证据；suspected_files 必须限制在 allowed_files 或日志明确指出的文件。
数据库未启动、端口占用、缺少环境变量等必须归为 environment_error，不得建议修改业务代码。
若失败涉及需求语义，保留 requirement_ids。只输出符合 Schema 的 JSON。"""


class RepairInput(BaseModel):
    diagnosis: DiagnoseOutput
    relevant_files: dict[str, str]
    allowed_files: list[str]
    immutable_files: list[str] = Field(default_factory=lambda: ["prd/**", "architecture/**"])
    attempt: int = Field(ge=1, default=1)
    max_attempts: int = Field(ge=1, default=3)


class RepairOutput(BaseModel):
    status: Literal["patched", "blocked", "no_change"]
    patch: str = ""
    changed_files: list[str] = Field(default_factory=list)
    explanation: str
    validation_commands: list[str] = Field(default_factory=list)
    blocker: dict[str, Any] = Field(default_factory=dict)


class RepairFailureSkill(LLMSkill):
    manifest = SkillManifest(
        id="devsmart.feedback.repair", name="Repair Build Failure", version="1.0.0",
        category=SkillCategory.TRANSFORM, description="在受限文件范围内生成最小 unified diff 修复补丁。",
        input_model=RepairInput, output_model=RepairOutput, tags=("feedback", "repair"),
    )
    temperature = 0.0

    @property
    def system_prompt(self) -> str:
        return """根据诊断生成最小 unified diff。
硬性规则：
- 只能修改 allowed_files；不得修改 immutable_files、PRD、Architecture 或契约来迁就代码。
- 不得删除/跳过测试、降低断言、硬编码测试结果、吞掉异常、全局关闭 lint、加入 test-only 业务分支。
- environment_error 应返回 blocked 或 no_change，不得修改业务代码。
- attempt >= max_attempts、需求冲突、必须改变架构决策或允许范围不足时返回 blocked。
- patch 必须是标准 unified diff；changed_files 必须与 patch 一致；给出重新验证命令。
只输出符合 Schema 的 JSON。"""
