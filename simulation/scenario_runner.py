"""Executor de cenários: roda sequências de ações em simuladores."""
from simulation.environment_simulator import EnvironmentSimulator
from typing import List, Callable, Optional


class Scenario:
    def __init__(self, name: str, initial_state: dict, actions: List[str],
                 success_condition: Callable = None):
        self.name = name
        self.initial_state = initial_state
        self.actions = actions
        self.success_condition = success_condition or (lambda state: True)


class ScenarioRunner:
    def __init__(self, sim: EnvironmentSimulator = None):
        self.sim = sim or EnvironmentSimulator()
        self.results: List[dict] = []

    def run(self, scenario: Scenario) -> dict:
        self.sim.reset()
        self.sim.set_state(**scenario.initial_state)
        transitions = []
        for action in scenario.actions:
            t = self.sim.step(action)
            transitions.append(t)
        success = scenario.success_condition(self.sim.state)
        result = {
            "scenario": scenario.name,
            "success": success,
            "steps": len(transitions),
            "total_reward": sum(t["reward"] for t in transitions),
            "final_state": dict(self.sim.state),
            "transitions": transitions,
        }
        self.results.append(result)
        return result

    def run_batch(self, scenarios: List[Scenario]) -> List[dict]:
        return [self.run(s) for s in scenarios]

    def report(self) -> dict:
        if not self.results:
            return {"message": "Nenhum cenário executado."}
        passed = sum(1 for r in self.results if r["success"])
        return {
            "total": len(self.results), "passed": passed, "failed": len(self.results) - passed,
            "avg_reward": sum(r["total_reward"] for r in self.results) / len(self.results),
        }
