from __future__ import annotations

from collections import defaultdict

from .errors import SkillNotFoundError
from .models import Skill


class SkillRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, dict[str, Skill]] = defaultdict(dict)

    def register(self, skill: Skill) -> None:
        versions = self._skills[skill.manifest.id]
        version = skill.manifest.version
        if version in versions:
            raise ValueError(f"Skill already registered: {skill.manifest.id}@{version}")
        versions[version] = skill

    def get(self, skill_id: str, version: str | None = None) -> Skill:
        versions = self._skills.get(skill_id)
        if not versions:
            raise SkillNotFoundError(skill_id)
        if version is not None:
            try:
                return versions[version]
            except KeyError as exc:
                raise SkillNotFoundError(f"{skill_id}@{version}") from exc
        latest = sorted(versions)[-1]
        return versions[latest]

    def list(self) -> list[Skill]:
        return [skill for versions in self._skills.values() for skill in versions.values()]
