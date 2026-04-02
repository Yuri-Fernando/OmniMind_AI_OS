"""Runner completo da arena: executa benchmark e exibe leaderboard."""
from arena.agent_arena import AgentArena
from arena.leaderboard import Leaderboard
from arena.tasks_dataset import get_tasks
from agents._llm_factory import get_llm


def make_agent_fn(provider: str, model: str):
    """Cria uma função de agente simples para benchmark."""
    llm = get_llm(provider, model)
    def agent_fn(question: str) -> str:
        return llm.invoke(question).content.strip()
    return agent_fn


class ArenaRunner:
    def __init__(self):
        self.arena = AgentArena()

    def add_competitor(self, name: str, provider: str, model: str):
        fn = make_agent_fn(provider, model)
        self.arena.register(name, fn)

    def run_benchmark(self, category: str = None, difficulty: str = None) -> dict:
        tasks = get_tasks(category=category, difficulty=difficulty)
        print(f"Executando {len(tasks)} tarefas com {len(self.arena.competitors)} agentes...")
        results = self.arena.run(tasks)
        board = Leaderboard(results)
        print("\n" + board.display())
        return {
            "tasks_run": len(tasks),
            "agents": len(self.arena.competitors),
            "results": results,
            "leaderboard": board.compute(),
        }


if __name__ == "__main__":
    runner = ArenaRunner()
    runner.add_competitor("ollama-mistral", "ollama", "mistral")
    runner.run_benchmark(difficulty="easy")
