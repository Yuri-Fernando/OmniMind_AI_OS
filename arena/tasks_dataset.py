"""Dataset de tarefas para benchmark de agentes."""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class BenchmarkTask:
    id: str
    category: str
    question: str
    expected_answer: str
    difficulty: str = "medium"  # easy | medium | hard
    tags: List[str] = field(default_factory=list)


# Dataset padrão de tarefas
DEFAULT_TASKS: List[BenchmarkTask] = [
    BenchmarkTask("t001", "math", "Quanto é 15 * 17?", "255", "easy", ["math", "arithmetic"]),
    BenchmarkTask("t002", "math", "Quanto é a raiz quadrada de 144?", "12", "easy", ["math"]),
    BenchmarkTask("t003", "geography", "Qual é a capital do Brasil?", "Brasília", "easy", ["geography"]),
    BenchmarkTask("t004", "geography", "Qual o maior país da América do Sul?", "Brasil", "easy", ["geography"]),
    BenchmarkTask("t005", "science", "Qual é a fórmula da água?", "H2O", "easy", ["science", "chemistry"]),
    BenchmarkTask("t006", "logic", "Se A > B e B > C, então A > C?", "Sim", "medium", ["logic"]),
    BenchmarkTask("t007", "math", "Qual é o resultado de 2^10?", "1024", "medium", ["math"]),
    BenchmarkTask("t008", "history", "Em que ano o Brasil foi descoberto?", "1500", "medium", ["history"]),
    BenchmarkTask("t009", "coding", "O que faz a função len() em Python?", "Retorna o comprimento de um objeto", "easy", ["coding"]),
    BenchmarkTask("t010", "reasoning", "João tem 3 filhos. Cada filho tem 2 irmãs. Quantas filhas João tem?", "2", "hard", ["reasoning", "logic"]),
]


def get_tasks(category: str = None, difficulty: str = None) -> List[BenchmarkTask]:
    tasks = DEFAULT_TASKS
    if category:
        tasks = [t for t in tasks if t.category == category]
    if difficulty:
        tasks = [t for t in tasks if t.difficulty == difficulty]
    return tasks
