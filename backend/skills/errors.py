class SkillError(Exception):
    """Base exception for all skill failures."""


class SkillNotFoundError(SkillError):
    pass


class SkillExecutionError(SkillError):
    pass


class SkillValidationError(SkillError):
    pass
