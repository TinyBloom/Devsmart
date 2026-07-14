from .architecture import GenerateArchitectureSkill, ValidateArchitectureSkill
from .codegen import GenerateCodePlanSkill, ValidateCodePlanSkill, DiagnoseFailureSkill, RepairFailureSkill
from .prd.skills import (
    GenerateHumanPrdSkill,
    GenerateMachinePrdSkill,
    ValidateHumanPrdSkill,
    ValidatePrdConsistencySkill,
    GenerateTestPlanSkill,
    TestExecutionFeedbackSkill,
    FixCodeFromFailureSkill,
)
from .registry import SkillRegistry
from .requirement.skills import (
    AnalyzeRequirementGapsSkill,
    GenerateNextQuestionSkill,
    UpdateStructuredRequirementsSkill,
    ValidateRequirementReadinessSkill,
)
from .tech.skills import (
    AnalyzeTechnicalConstraintsSkill,
    GenerateArchitectureDecisionRecordSkill,
    RecommendTechStackSkill,
    ValidateTechStackCompatibilitySkill,
)


def build_default_registry() -> SkillRegistry:
    registry = SkillRegistry()
    for skill in (
        AnalyzeRequirementGapsSkill(),
        GenerateNextQuestionSkill(),
        UpdateStructuredRequirementsSkill(),
        ValidateRequirementReadinessSkill(),
        GenerateHumanPrdSkill(),
        ValidateHumanPrdSkill(),
        GenerateMachinePrdSkill(),
        ValidatePrdConsistencySkill(),
        GenerateTestPlanSkill(),
        TestExecutionFeedbackSkill(),
        FixCodeFromFailureSkill(),
        AnalyzeTechnicalConstraintsSkill(),
        RecommendTechStackSkill(),
        ValidateTechStackCompatibilitySkill(),
        GenerateArchitectureDecisionRecordSkill(),
        GenerateArchitectureSkill(),
        ValidateArchitectureSkill(),
        GenerateCodePlanSkill(),
        ValidateCodePlanSkill(),
        DiagnoseFailureSkill(),
        RepairFailureSkill(),
    ):
        registry.register(skill)
    return registry
