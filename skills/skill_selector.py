"""Seletor semântico de skills: encontra a skill mais adequada para uma tarefa."""
from typing import List, Optional
from skills.skill_registry import SkillRegistry, Skill
from agents._llm_factory import get_llm


class SkillSelector:
    def __init__(self, registry: SkillRegistry, provider: str = "ollama", model: str = "mistral"):
        self.registry = registry
        self.llm = get_llm(provider, model)

    def select(self, task: str) -> Optional[Skill]:
        skills = self.registry.all()
        if not skills:
            return None
        skills_list = "\n".join(f"- {s['name']}: {s['description']}" for s in skills)
        prompt = (
            f"Dado a tarefa: '{task}'\n\nEscolha a skill mais adequada da lista abaixo.\n"
            f"Responda APENAS com o nome exato da skill.\n\n{skills_list}"
        )
        response = self.llm.invoke(prompt).content.strip().split()[0]
        return self.registry.get(response)

    def select_and_execute(self, task: str, *args, **kwargs):
        skill = self.select(task)
        if not skill:
            return {"error": "Nenhuma skill disponível"}
        return {
            "skill": skill.name,
            "result": self.registry.execute(skill.name, *args, **kwargs)
        }
