"""Recupera informações do grafo de conhecimento."""
from typing import List
from knowledge_graph.graph_builder import KnowledgeGraphBuilder


class GraphRetriever:
    def __init__(self, builder: KnowledgeGraphBuilder = None):
        self.builder = builder or KnowledgeGraphBuilder()

    def get_neighbors(self, entity: str) -> List[dict]:
        """Retorna nós diretamente conectados a uma entidade."""
        neighbors = []
        for edge in self.builder.edges:
            if edge["source"].lower() == entity.lower():
                neighbors.append({"entity": edge["target"], "relation": edge["relation"], "direction": "out"})
            elif edge["target"].lower() == entity.lower():
                neighbors.append({"entity": edge["source"], "relation": edge["relation"], "direction": "in"})
        return neighbors

    def find_path(self, start: str, end: str, max_hops: int = 3) -> List[str]:
        """BFS para encontrar caminho entre dois nós."""
        from collections import deque
        visited = set()
        queue = deque([[start]])
        while queue:
            path = queue.popleft()
            node = path[-1]
            if node.lower() == end.lower():
                return path
            if len(path) > max_hops or node in visited:
                continue
            visited.add(node)
            for nb in self.get_neighbors(node):
                queue.append(path + [nb["entity"]])
        return []

    def search(self, query: str) -> List[dict]:
        """Busca textual simples nos nós."""
        q = query.lower()
        return [n for n in self.builder.nodes.values() if q in n["name"].lower()]

    def context_for_query(self, query: str) -> str:
        nodes = self.search(query)
        if not nodes:
            return ""
        lines = []
        for node in nodes[:3]:
            neighbors = self.get_neighbors(node["name"])
            rels = "; ".join(f"{nb['relation']} → {nb['entity']}" for nb in neighbors[:3])
            lines.append(f"{node['name']} ({node['type']}): {rels or 'sem relações'}")
        return "\n".join(lines)
