"""Carrega skills de módulos Python e as registra automaticamente."""
import importlib, os, inspect
from skills.skill_registry import SkillRegistry


def load_skills_from_module(module_path: str, registry: SkillRegistry) -> int:
    """Importa um módulo e registra todas as funções públicas como skills."""
    module = importlib.import_module(module_path)
    count = 0
    for name, obj in inspect.getmembers(module, inspect.isfunction):
        if not name.startswith("_"):
            doc = obj.__doc__ or f"Skill: {name}"
            registry.register(name, doc.strip().split("\n")[0], obj)
            count += 1
    return count


def load_skills_from_directory(directory: str, registry: SkillRegistry, package: str = "") -> dict:
    """Carrega skills de todos os arquivos .py em um diretório."""
    results = {}
    for fname in os.listdir(directory):
        if fname.endswith(".py") and not fname.startswith("_"):
            module_name = f"{package}.{fname[:-3]}" if package else fname[:-3]
            try:
                n = load_skills_from_module(module_name, registry)
                results[fname] = n
            except Exception as e:
                results[fname] = f"ERRO: {e}"
    return results
