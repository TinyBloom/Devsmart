from __future__ import annotations

from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field

from ..base import BaseSkill, LLMSkill
from ..models import Artifact, SkillCategory, SkillContext, SkillManifest, SkillResult


class GenerateHumanPrdInput(BaseModel):
    project_name: str
    requirements: dict[str, Any]


class GenerateHumanPrdOutput(BaseModel):
    title: str
    markdown: str


class GenerateHumanPrdSkill(LLMSkill):
    manifest = SkillManifest(
        id="devsmart.prd.generate-human", name="Generate Human PRD", version="1.0.0",
        category=SkillCategory.GENERATE, description="从已确认需求生成面向人的 Markdown PRD。",
        input_model=GenerateHumanPrdInput, output_model=GenerateHumanPrdOutput, tags=("prd",),
    )

    @property
    def system_prompt(self) -> str:
        return """根据结构化需求生成可评审 PRD。**必须在文档开头包含目录（Table of Contents）**，目录使用 Markdown 链接格式指向各个章节。

必须包含以下章节：

1. 产品概述：背景与目标、非目标、用户与场景
2. 功能模块：功能需求、业务规则
3. 数据模型：数据实体和字段定义
4. API 接口清单：所有接口的请求体和响应体
5. 非功能需求：性能、安全等
6. 外部集成
7. 测试计划：7.1单元测试、7.2集成测试、7.3 Playwright端到端测试、7.4测试结果循环（CI反馈机制）

## 必须补充的关键内容（严重缺失会导致生成质量极差）：

8. 工程目录结构：
   - 后端目录：src/handlers/ src/models/ src/auth/ src/error/ src/db/ main.rs
   - 前端目录：src/views/ src/components/ src/stores/ src/api/ src/router/ src/types/

9. 统一错误响应格式：
   - 错误响应 JSON 结构：{"code": "业务错误码", "message": "用户友好提示", "request_id": "uuid"}
   - HTTP 状态码映射：400参数错误 / 401未认证 / 403无权限 / 404资源不存在 / 500服务器错误

10. API 响应体定义：
    - 分页响应格式：{"data": [...], "total": N, "page": N, "page_size": N, "total_pages": N}
    - 每个接口必须提供完整的成功响应体示例

11. 数据库建表 SQL：
    - CREATE TABLE SQL（含 UNIQUE、NOT NULL、DEFAULT、FOREIGN KEY）
    - 性能索引定义（复合索引、单字段索引）

12. 前端页面清单和路由定义：
    - 每个页面的路由路径、页面组件名称、页面包含的功能区块

13. 测试用例规范：
    - 关键测试场景（正常路径、边界条件、异常情况、权限验证）

目录格式示例：
## 目录
- [1. 产品概述](#1-产品概述)
- [2. 功能模块](#2-功能模块)
...

不得虚构已确认事实；未知项列入开放问题。JSON 中 markdown 字段承载完整 Markdown。"""

    async def execute(self, context: SkillContext, skill_input: GenerateHumanPrdInput) -> SkillResult:
        result = await super().execute(context, skill_input)
        result.artifacts.append(Artifact(type="human_prd", path="prd/human-prd.md", content=result.output["markdown"], media_type="text/markdown"))
        return result


class PrdIssue(BaseModel):
    section: str
    message: str
    severity: Literal["warning", "error"]


class ValidateHumanPrdInput(BaseModel):
    markdown: str


class ValidateHumanPrdOutput(BaseModel):
    valid: bool
    issues: list[PrdIssue] = Field(default_factory=list)
    present_sections: list[str] = Field(default_factory=list)


class ValidateHumanPrdSkill(BaseSkill):
    manifest = SkillManifest(
        id="devsmart.prd.validate-human", name="Validate Human PRD", version="1.0.0",
        category=SkillCategory.VALIDATE, description="确定性检查 Markdown PRD 的必要章节。",
        input_model=ValidateHumanPrdInput, output_model=ValidateHumanPrdOutput, tags=("prd", "validator"),
    )

    async def execute(self, context: SkillContext, skill_input: ValidateHumanPrdInput) -> SkillResult:
        aliases = {
            "目标": ("目标", "goals"), "用户": ("用户", "user"), "功能": ("功能", "feature"),
            "验收标准": ("验收", "acceptance"), "非功能": ("非功能", "non-functional"),
        }
        lower = skill_input.markdown.lower()
        present = [name for name, words in aliases.items() if any(word.lower() in lower for word in words)]
        issues = [PrdIssue(section=name, message=f"缺少或无法识别章节：{name}", severity="error") for name in aliases if name not in present]
        output = ValidateHumanPrdOutput(valid=not issues, issues=issues, present_sections=present)
        return SkillResult(output=output.model_dump(mode="json"))


class GenerateMachinePrdInput(BaseModel):
    project_name: str
    human_prd: str
    requirements: dict[str, Any]


class GenerateMachinePrdOutput(BaseModel):
    schema_version: str = "1.0"
    product: dict[str, Any]
    assumptions: list[dict[str, Any]] = Field(default_factory=list)
    open_questions: list[dict[str, Any]] = Field(default_factory=list)
    glossary: dict[str, str] = Field(default_factory=dict)
    actors: list[dict[str, Any]] = Field(default_factory=list)
    modules: list[dict[str, Any]] = Field(default_factory=list)
    use_cases: list[dict[str, Any]] = Field(default_factory=list)
    features: list[dict[str, Any]] = Field(default_factory=list)
    business_rules: list[dict[str, Any]] = Field(default_factory=list)
    permissions: list[dict[str, Any]] = Field(default_factory=list)
    domain_models: list[dict[str, Any]] = Field(default_factory=list)
    database_models: list[dict[str, Any]] = Field(default_factory=list)
    api_contracts: list[dict[str, Any]] = Field(default_factory=list)
    error_catalog: list[dict[str, Any]] = Field(default_factory=list)
    events: list[dict[str, Any]] = Field(default_factory=list)
    non_functional_requirements: list[dict[str, Any]] = Field(default_factory=list)
    acceptance_criteria: list[dict[str, Any]] = Field(default_factory=list)
    test_requirements: list[dict[str, Any]] = Field(default_factory=list)
    traceability: dict[str, Any] = Field(default_factory=dict)
    project_structure: dict[str, Any] = Field(default_factory=dict)
    error_format: dict[str, Any] = Field(default_factory=dict)
    api_responses: list[dict[str, Any]] = Field(default_factory=list)
    database_schema: dict[str, Any] = Field(default_factory=dict)
    frontend_routes: list[dict[str, Any]] = Field(default_factory=list)
    test_specifications: list[dict[str, Any]] = Field(default_factory=list)


class GenerateMachinePrdSkill(LLMSkill):
    manifest = SkillManifest(
        id="devsmart.prd.generate-machine", name="Generate Machine PRD", version="1.0.0",
        category=SkillCategory.TRANSFORM, description="将人类 PRD 转为稳定的机器可读模型。",
        input_model=GenerateMachinePrdInput, output_model=GenerateMachinePrdOutput, tags=("prd", "structured-output"),
    )

    @property
    def system_prompt(self) -> str:
        return """将 Human PRD 转换为可直接驱动架构和代码生成的 Machine PRD 工程契约。
硬性要求：
1. 所有 feature、use_case、business_rule、domain_model、database_model、api_contract、acceptance_criterion、test_requirement 必须有稳定、唯一、字符串 ID；禁止 UUID 对象作为字典 key。
2. business_rules 明确定义前置条件、不变量、状态流转、边界、违反规则的 error_code；不得把业务规则藏在描述文本中。
3. domain_models 描述聚合、值对象、命令、状态机和不变量；database_models 单独描述表、字段、约束、索引、外键、软删除和历史快照策略。
4. api_contracts 必须达到 JSON Schema/OpenAPI 精度：method、path、认证、权限、path/query/body、成功与错误响应、事务、幂等和副作用。
5. 请求 DTO、响应 DTO 和数据库实体必须分离；敏感字段不得进入响应。
6. error_catalog 统一定义 code、HTTP status、message、details schema；API 引用的错误码必须存在。
7. permissions 明确角色、资源、动作、数据范围和条件。
8. acceptance_criteria 必须可自动测试，并关联 feature_id；建议同时关联 rule_ids/api_ids，使用 given/when/then。
9. test_requirements 覆盖正常、边界、异常、权限、事务和契约测试；traceability 建立需求到 API、代码任务和测试的映射入口。
10. assumptions 与 open_questions 必须结构化；关键未知项标记 blocking=true，禁止自行猜测。
11. non_functional_requirements 必须量化性能、安全、可靠性、容量、可观测性和兼容性指标。
12. 保留旧字段用于兼容，但新生成内容应以 modules/use_cases/business_rules/domain_models/database_models/api_contracts/error_catalog/test_requirements 为主。
只输出符合 Schema 的 JSON。"""

    async def execute(self, context: SkillContext, skill_input: GenerateMachinePrdInput) -> SkillResult:
        result = await super().execute(context, skill_input)
        content = yaml.safe_dump(result.output, allow_unicode=True, sort_keys=False)
        result.artifacts.append(Artifact(type="machine_prd", path="prd/machine-prd.yaml", content=content, media_type="application/yaml"))
        return result


class ValidatePrdConsistencyInput(BaseModel):
    human_prd: str
    machine_prd: GenerateMachinePrdOutput


class ConsistencyIssue(BaseModel):
    code: str
    message: str
    severity: Literal["warning", "error"]
    reference_id: str | None = None


class ValidatePrdConsistencyOutput(BaseModel):
    valid: bool
    issues: list[ConsistencyIssue] = Field(default_factory=list)
    coverage: float = Field(ge=0, le=1)


class ValidatePrdConsistencySkill(BaseSkill):
    manifest = SkillManifest(
        id="devsmart.prd.validate-consistency", name="Validate PRD Consistency", version="1.0.0",
        category=SkillCategory.VALIDATE, description="检查 Machine PRD 的引用完整性和验收覆盖率。",
        input_model=ValidatePrdConsistencyInput, output_model=ValidatePrdConsistencyOutput, tags=("prd", "validator"),
    )

    async def execute(self, context: SkillContext, skill_input: ValidatePrdConsistencyInput) -> SkillResult:
        m = skill_input.machine_prd
        issues: list[ConsistencyIssue] = []

        collections = {
            "feature": m.features,
            "use_case": m.use_cases,
            "business_rule": m.business_rules,
            "domain_model": m.domain_models,
            "database_model": m.database_models,
            "api_contract": m.api_contracts,
            "acceptance_criterion": m.acceptance_criteria,
            "test_requirement": m.test_requirements,
        }
        all_ids: dict[str, str] = {}
        for kind, items in collections.items():
            local: set[str] = set()
            for item in items:
                raw = item.get("id")
                if not isinstance(raw, str) or not raw.strip():
                    issues.append(ConsistencyIssue(code="missing_stable_id", message=f"{kind} 缺少稳定字符串 ID", severity="error"))
                    continue
                item_id = raw.strip()
                if item_id in local or item_id in all_ids:
                    issues.append(ConsistencyIssue(code="duplicate_id", message=f"ID 重复：{item_id}", severity="error", reference_id=item_id))
                local.add(item_id); all_ids[item_id] = kind

        feature_ids = {str(x.get("id")) for x in m.features if x.get("id")}
        covered: set[str] = set()
        for criterion in m.acceptance_criteria:
            ref = criterion.get("feature_id")
            if ref and str(ref) not in feature_ids:
                issues.append(ConsistencyIssue(code="unknown_feature_reference", message=f"验收标准引用不存在的功能：{ref}", severity="error", reference_id=str(ref)))
            elif ref:
                covered.add(str(ref))
        for feature_id in feature_ids - covered:
            issues.append(ConsistencyIssue(code="feature_without_acceptance", message=f"功能没有验收标准：{feature_id}", severity="error", reference_id=feature_id))

        error_codes = {str(x.get("code")) for x in m.error_catalog if x.get("code")}
        for api in m.api_contracts:
            api_id = str(api.get("id") or "unknown")
            if not api.get("method") or not api.get("path"):
                issues.append(ConsistencyIssue(code="incomplete_api_contract", message=f"API {api_id} 缺少 method/path", severity="error", reference_id=api_id))
            if not api.get("responses"):
                issues.append(ConsistencyIssue(code="missing_api_responses", message=f"API {api_id} 缺少响应契约", severity="error", reference_id=api_id))
            refs = api.get("error_codes", [])
            responses = api.get("responses", {})
            if isinstance(responses, dict):
                for value in responses.values():
                    if isinstance(value, dict): refs += value.get("error_codes", []) or []
            for code in refs:
                if str(code) not in error_codes:
                    issues.append(ConsistencyIssue(code="unknown_error_code", message=f"API {api_id} 引用未定义错误码：{code}", severity="error", reference_id=api_id))

        for rule in m.business_rules:
            rule_id = str(rule.get("id") or "unknown")
            if not (rule.get("violation_error") or rule.get("error_code")):
                issues.append(ConsistencyIssue(code="rule_without_error", message=f"业务规则 {rule_id} 未定义违反规则时的错误", severity="warning", reference_id=rule_id))

        if any(bool(q.get("blocking")) for q in m.open_questions if isinstance(q, dict)):
            issues.append(ConsistencyIssue(code="blocking_open_question", message="Machine PRD 存在阻塞性开放问题", severity="error"))

        coverage = len(covered & feature_ids) / len(feature_ids) if feature_ids else 0.0
        output = ValidatePrdConsistencyOutput(valid=not any(i.severity == "error" for i in issues), issues=issues, coverage=coverage)
        return SkillResult(output=output.model_dump(mode="json"))



class GenerateTestPlanInput(BaseModel):
    project_name: str
    human_prd: str
    machine_prd: GenerateMachinePrdOutput


class TestCase(BaseModel):
    feature_id: str
    test_name: str
    test_description: str
    test_file: str


class PlaywrightTestCase(TestCase):
    test_scenarios: list[str] = Field(default_factory=list)


class TestPlanOutput(BaseModel):
    unit_tests: list[TestCase] = Field(default_factory=list)
    integration_tests: list[TestCase] = Field(default_factory=list)
    playwright_tests: list[PlaywrightTestCase] = Field(default_factory=list)


class GenerateTestPlanSkill(LLMSkill):
    manifest = SkillManifest(
        id="devsmart.prd.generate-test-plan", name="Generate Test Plan", version="1.0.0",
        category=SkillCategory.GENERATE, description="根据 PRD 生成完整的测试计划，包含单元测试、集成测试和 Playwright 端到端测试。",
        input_model=GenerateTestPlanInput, output_model=TestPlanOutput, tags=("prd", "test"),
    )

    @property
    def system_prompt(self) -> str:
        return """根据 PRD 生成完整的测试计划。
单元测试：针对每个核心功能模块，生成独立的单元测试用例，覆盖函数/方法的正常路径和边界条件。测试文件路径应遵循项目规范（如 tests/unit/）。

集成测试：针对模块间交互、数据库操作、API调用等，生成集成测试用例。测试文件路径应遵循项目规范（如 tests/integration/）。

Playwright端到端测试：针对用户完整流程，生成浏览器自动化测试用例，包含页面导航、表单填写、按钮点击等场景。测试文件路径应遵循项目规范（如 tests/e2e/）。

每个测试用例必须包含：feature_id（关联的功能ID）、test_name（测试名称）、test_description（测试描述）、test_file（测试文件路径）。Playwright测试还需包含test_scenarios（测试场景步骤）。"""

    async def execute(self, context: SkillContext, skill_input: GenerateTestPlanInput) -> SkillResult:
        result = await super().execute(context, skill_input)
        return result


class TestFailure(BaseModel):
    test_name: str
    error_type: str
    error_message: str
    stack_trace: str
    affected_file: str
    affected_line: Optional[int] = None


class TestExecutionResult(BaseModel):
    test_type: Literal["unit", "integration", "e2e"]
    command: str
    passed: bool
    total_tests: int
    passed_count: int
    failed_count: int
    failures: list[TestFailure] = Field(default_factory=list)
    output: str
    execution_time: float


class TestExecutionFeedbackInput(BaseModel):
    test_output: str
    test_type: Literal["unit", "integration", "e2e"]
    command: str


class TestExecutionFeedbackOutput(BaseModel):
    result: TestExecutionResult
    all_passed: bool
    retry_needed: bool
    retry_count: int = 0


class TestExecutionFeedbackSkill(LLMSkill):
    manifest = SkillManifest(
        id="devsmart.prd.test-execution-feedback", name="Test Execution Feedback", version="1.0.0",
        category=SkillCategory.VALIDATE, description="解析测试执行输出，提取失败信息，判断是否需要重试。",
        input_model=TestExecutionFeedbackInput, output_model=TestExecutionFeedbackOutput, tags=("prd", "test", "feedback"),
    )

    @property
    def system_prompt(self) -> str:
        return """解析测试执行输出，提取详细的失败信息。

输入：测试命令的完整输出文本
输出：结构化的测试执行结果

解析规则：
1. 识别测试类型（单元测试/集成测试/e2e测试）
2. 统计通过和失败的测试数量
3. 对于每个失败的测试，提取：
   - test_name：测试名称
   - error_type：错误类型（如 AssertionError、AttributeError、KeyError 等）
   - error_message：错误消息
   - stack_trace：堆栈跟踪信息
   - affected_file：受影响的代码文件路径
   - affected_line：受影响的代码行号（如果可识别）
4. 判断是否所有测试都通过
5. 判断是否需要重试（存在失败时返回 True）

请输出结构化的 JSON 结果。"""

    async def execute(self, context: SkillContext, skill_input: TestExecutionFeedbackInput) -> SkillResult:
        result = await super().execute(context, skill_input)
        return result


class FixCodeFromFailureInput(BaseModel):
    project_name: str
    test_failures: list[TestFailure]
    human_prd: str
    machine_prd: GenerateMachinePrdOutput


class CodeFix(BaseModel):
    file_path: str
    old_code: str
    new_code: str
    fix_description: str


class FixCodeFromFailureOutput(BaseModel):
    fixes: list[CodeFix] = Field(default_factory=list)
    fix_summary: str
    success: bool


class FixCodeFromFailureSkill(LLMSkill):
    manifest = SkillManifest(
        id="devsmart.prd.fix-code-from-failure", name="Fix Code From Failure", version="1.0.0",
        category=SkillCategory.GENERATE, description="根据测试失败分析结果，生成代码修复补丁。",
        input_model=FixCodeFromFailureInput, output_model=FixCodeFromFailureOutput, tags=("prd", "test", "fix"),
    )

    @property
    def system_prompt(self) -> str:
        return """根据测试失败分析结果，生成代码修复补丁。

输入：测试失败列表，每个失败包含错误类型、错误消息、堆栈跟踪、受影响的文件和行号
输出：代码修复补丁列表

修复规则：
1. 分析每个测试失败的根本原因
2. 定位问题代码位置（根据堆栈跟踪和受影响文件）
3. 生成最小化的代码修复：
   - file_path：需要修改的文件路径
   - old_code：需要替换的代码片段
   - new_code：替换后的代码片段
   - fix_description：修复描述
4. 确保修复不会引入新的问题
5. 保持代码风格与项目一致

请输出结构化的 JSON 结果，包含修复补丁列表和修复摘要。"""

    async def execute(self, context: SkillContext, skill_input: FixCodeFromFailureInput) -> SkillResult:
        result = await super().execute(context, skill_input)
        return result


class GenerateDeltaPrdInput(BaseModel):
    project_name: str
    previous_prd: dict[str, Any]
    requirements: dict[str, Any]
    delta_type: Literal["FEATURE_ADDITION", "BUG_FIX", "REFACTOR", "ENHANCEMENT"]


class GenerateDeltaPrdOutput(BaseModel):
    delta_type: str
    version: int
    previous_version: int
    changes_summary: str
    new_features: list[dict[str, Any]] = Field(default_factory=list)
    bug_fixes: list[dict[str, Any]] = Field(default_factory=list)
    enhancements: list[dict[str, Any]] = Field(default_factory=list)
    refactors: list[dict[str, Any]] = Field(default_factory=list)
    impacted_modules: list[str] = Field(default_factory=list)
    related_features: list[str] = Field(default_factory=list)
    backward_compatibility: str = "yes"
    migration_notes: list[str] = Field(default_factory=list)


class GenerateDeltaPrdSkill(LLMSkill):
    manifest = SkillManifest(
        id="devsmart.prd.generate-delta", name="Generate Delta PRD", version="1.0.0",
        category=SkillCategory.GENERATE, description="为现有项目生成增量 PRD，支持新增功能和 Bug 修复。",
        input_model=GenerateDeltaPrdInput, output_model=GenerateDeltaPrdOutput, tags=("prd", "delta"),
    )

    @property
    def system_prompt(self) -> str:
        return """根据现有 PRD 和新增需求生成增量 PRD。

输入：
- previous_prd：历史 PRD 的完整内容（机器可读格式）
- requirements：新增需求描述
- delta_type：变更类型（FEATURE_ADDITION/BUG_FIX/REFACTOR/ENHANCEMENT）

输出：结构化的增量 PRD

生成规则：
1. 分析新增需求与现有 PRD 的关系，识别受影响的模块和关联功能
2. 生成变更摘要，明确本次变更的核心内容
3. 根据变更类型分类输出：
   - new_features：新增功能列表
   - bug_fixes：Bug 修复列表（包含问题描述、严重程度）
   - enhancements：功能增强列表
   - refactors：代码重构列表
4. 分析影响范围：
   - impacted_modules：受影响的模块名称列表
   - related_features：关联的现有功能名称列表
5. 评估向后兼容性，提供迁移说明
6. 保持与历史 PRD 的一致性，不重复已有内容

请输出结构化的 JSON 结果。"""

    async def execute(self, context: SkillContext, skill_input: GenerateDeltaPrdInput) -> SkillResult:
        result = await super().execute(context, skill_input)
        content = yaml.safe_dump(result.output, allow_unicode=True, sort_keys=False)
        result.artifacts.append(Artifact(type="delta_prd", path="prd/delta-prd.yaml", content=content, media_type="application/yaml"))
        return result
