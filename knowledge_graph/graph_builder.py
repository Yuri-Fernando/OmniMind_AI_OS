"""Constrói grafo de conhecimento a partir de texto e entidades."""
from typing import List, Dict, Tuple
from agents._llm_factory import get_llm
from knowledge_graph.entity_extractor import EntityExtractor


class KnowledgeGraphBuilder:
    def __init__(self, provider: str = "ollama", model: str = "mistral"):
        self.llm = get_llm(provider, model)
        self.extractor = EntityExtractor(provider, model)
        self.nodes: Dict[str, dict] = {}
        self.edges: List[dict] = []

    def add_text(self, text: str, source: str = ""):
        entities = self.extractor.extract(text)
        for ent in entities:
            name = ent["text"]
            if name not in self.nodes:
                self.nodes[name] = {"name": name, "type": ent.get("label", "unknown"), "source": source}
        # Extrai relações via LLM
        if len(entities) >= 2:
            self._extract_relations(text, entities)

    def _extract_relations(self, text: str, entities: List[dict]):
        names = ", ".join(e["text"] for e in entities[:10])
        prompt = (
            f"Dado o texto: '{text[:500]}'\n"
            f"E as entidades: {names}\n\n"
            f"Liste as relações entre entidades no formato: ENTIDADE1 | RELAÇÃO | ENTIDADE2\n"
            f"Máximo 5 relações."
        )
        response = self.llm.invoke(prompt).content.strip()
        for line in response.split("\n"):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) == 3:
                self.edges.append({"source": parts[0], "relation": parts[1], "target": parts[2]})

    def to_dict(self) -> dict:
        return {"nodes": list(self.nodes.values()), "edges": self.edges}

    def stats(self) -> dict:
        return {"nodes": len(self.nodes), "edges": len(self.edges)}
