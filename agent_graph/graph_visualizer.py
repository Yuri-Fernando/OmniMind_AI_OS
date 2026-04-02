"""Visualizador do grafo de execução do agente."""
from typing import Dict, List, Optional


class GraphVisualizer:
    """Gera representações visuais do grafo de execução."""

    def __init__(self):
        self.nodes: List[dict] = []
        self.edges: List[dict] = []

    def add_node(self, node_id: str, label: str, node_type: str = "step"):
        self.nodes.append({"id": node_id, "label": label, "type": node_type})

    def add_edge(self, from_id: str, to_id: str, label: str = ""):
        self.edges.append({"from": from_id, "to": to_id, "label": label})

    def to_mermaid(self) -> str:
        """Gera diagrama Mermaid."""
        lines = ["graph TD"]
        for node in self.nodes:
            shape = f'["{node["label"]}"]' if node["type"] == "step" else f'(("{node["label"]}"))'
            lines.append(f'    {node["id"]}{shape}')
        for edge in self.edges:
            label = f'|"{edge["label"]}"|' if edge["label"] else ""
            lines.append(f'    {edge["from"]} --{label}--> {edge["to"]}')
        return "\n".join(lines)

    def to_ascii(self) -> str:
        """Representação ASCII do grafo."""
        lines = ["=== Grafo de Execução ==="]
        node_map = {n["id"]: n["label"] for n in self.nodes}
        for edge in self.edges:
            src = node_map.get(edge["from"], edge["from"])
            dst = node_map.get(edge["to"], edge["to"])
            label = f" [{edge['label']}]" if edge["label"] else ""
            lines.append(f"  {src} -->{label} {dst}")
        return "\n".join(lines)

    def from_langchain_graph(self, graph) -> "GraphVisualizer":
        """Constrói visualização a partir de um LangGraph compilado."""
        try:
            for node_name in graph.nodes:
                self.add_node(node_name, node_name)
            for edge in graph.edges:
                self.add_edge(edge[0], edge[1])
        except Exception as e:
            self.add_node("error", f"Erro: {e}", "error")
        return self
