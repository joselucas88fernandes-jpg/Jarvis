from typing import Callable, Dict, Any

class SkillRegistry:
    def __init__(self):
        self._skills: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, domain: str, entrypoint: Callable):
        if domain not in self._skills:
            self._skills[domain] = {}
        self._skills[domain][name] = entrypoint

    def get_skill(self, domain: str, name: str) -> Callable:
        return self._skills.get(domain, {}).get(name)

skill_registry = SkillRegistry()
