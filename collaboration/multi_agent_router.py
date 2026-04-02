"""Roteador multi-agente: distribui tarefas para o agente mais adequado."""
from collaboration.agent_registry import AgentRegistry, AgentInfo
from collaboration.communication_protocol import MessageBus, AgentMessage
from typing import Optional


class MultiAgentRouter:
    def __init__(self):
        self.registry = AgentRegistry()
        self.bus = MessageBus()

    def register_agent(self, name: str, capabilities: list, handler=None):
        self.registry.register(name, capabilities, handler)

    def route(self, task: str, required_capability: Optional[str] = None) -> dict:
        """Envia tarefa para o agente mais adequado e retorna resultado."""
        if required_capability:
            candidates = self.registry.find_by_capability(required_capability)
        else:
            candidates = self.registry.available()

        if not candidates:
            return {"error": "Nenhum agente disponível", "task": task}

        # Seleciona agente com menos tarefas executadas
        agent = min(candidates, key=lambda a: a.task_count)

        self.registry.set_status(agent.name, "busy")
        result = {"agent": agent.name, "task": task, "output": None, "status": "failed"}

        try:
            if agent.handler:
                output = agent.handler(task)
                result["output"] = output
                result["status"] = "success"
            else:
                result["output"] = f"[{agent.name}] sem handler configurado"
                result["status"] = "no_handler"
            agent.task_count += 1
        except Exception as e:
            result["error"] = str(e)
        finally:
            self.registry.set_status(agent.name, "idle")

        # Registra no bus
        msg = AgentMessage(sender="router", recipient=agent.name,
                           content=task, msg_type="task")
        self.bus.send(msg)
        return result

    def broadcast_task(self, task: str) -> list:
        agents = self.registry.available()
        return [self.route(task) for a in agents]
