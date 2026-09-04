"""
knowledge_graph/graph_builder_neo4j_v2.py

V2 do Knowledge Graph: a V1 (graph_builder.py + graph_retriever.py) guarda
nós e arestas em dicionários/listas Python em memória -- some quando o
processo termina, e `find_path` faz um BFS manual em Python sobre uma lista
de arestas.

Esta V2 mantém a mesma extração de entidades/relações via LLM
(reaproveita `EntityExtractor`, sem duplicar essa lógica) mas persiste o
grafo em **Neo4j**, com nós e relações reais no banco, e usa Cypher nativo
para vizinhança e caminho mais curto -- o mesmo grafo fica disponível entre
sessões e pode ser consultado fora do processo do agente (Neo4j Browser,
outras aplicações).

Uso:
    from knowledge_graph.graph_builder_neo4j_v2 import Neo4jKnowledgeGraphBuilder

    kg = Neo4jKnowledgeGraphBuilder(uri="bolt://localhost:7687", auth=("neo4j", "senha"))
    kg.add_text("Marie Curie trabalhou com Pierre Curie na Sorbonne.", source="bio.txt")
    kg.stats()
"""

import os
from typing import Dict, List

from neo4j import GraphDatabase

from knowledge_graph.entity_extractor import EntityExtractor


class Neo4jKnowledgeGraphBuilder:
    def __init__(
        self,
        uri: str = None,
        auth: tuple = None,
        provider: str = "ollama",
        model: str = "mistral",
    ):
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.auth = auth or (
            os.getenv("NEO4J_USER", "neo4j"),
            os.getenv("NEO4J_PASSWORD", "neo4j"),
        )
        self._driver = GraphDatabase.driver(self.uri, auth=self.auth)
        self.extractor = EntityExtractor(provider, model)
        self._ensure_constraints()

    def _ensure_constraints(self):
        with self._driver.session() as session:
            session.run(
                "CREATE CONSTRAINT entity_name IF NOT EXISTS "
                "FOR (e:Entity) REQUIRE e.name IS UNIQUE"
            )

    def add_text(self, text: str, source: str = ""):
        entities = self.extractor.extract(text)
        with self._driver.session() as session:
            for ent in entities:
                session.execute_write(self._merge_entity, ent["text"], ent.get("label", "unknown"), source)

        if len(entities) >= 2:
            self._extract_and_store_relations(text, entities)

    @staticmethod
    def _merge_entity(tx, name: str, entity_type: str, source: str):
        tx.run(
            """
            MERGE (e:Entity {name: $name})
            SET e.type = $type, e.source = $source
            """,
            name=name,
            type=entity_type,
            source=source,
        )

    def _extract_and_store_relations(self, text: str, entities: List[dict]):
        names = ", ".join(e["text"] for e in entities[:10])
        prompt = (
            f"Dado o texto: '{text[:500]}'\n"
            f"E as entidades: {names}\n\n"
            f"Liste as relações entre entidades no formato: ENTIDADE1 | RELAÇÃO | ENTIDADE2\n"
            f"Máximo 5 relações."
        )
        response = self.extractor.llm.invoke(prompt).content.strip()

        with self._driver.session() as session:
            for line in response.split("\n"):
                parts = [p.strip() for p in line.split("|")]
                if len(parts) == 3:
                    source_name, relation, target_name = parts
                    session.execute_write(self._merge_relation, source_name, relation, target_name)

    @staticmethod
    def _merge_relation(tx, source_name: str, relation: str, target_name: str):
        # relação armazenada como tipo dinâmico via APOC seria ideal; para manter a
        # dependência mínima (sem exigir plugin APOC), guarda como propriedade de
        # uma relação genérica RELATES_TO -- mantém Cypher padrão.
        tx.run(
            """
            MERGE (a:Entity {name: $source_name})
            MERGE (b:Entity {name: $target_name})
            MERGE (a)-[r:RELATES_TO {relation: $relation}]->(b)
            """,
            source_name=source_name,
            target_name=target_name,
            relation=relation,
        )

    def stats(self) -> Dict[str, int]:
        with self._driver.session() as session:
            nodes = session.run("MATCH (e:Entity) RETURN count(e) AS n").single()["n"]
            edges = session.run("MATCH ()-[r:RELATES_TO]->() RETURN count(r) AS n").single()["n"]
        return {"nodes": nodes, "edges": edges}

    def close(self):
        self._driver.close()


class Neo4jGraphRetriever:
    """Substitui o BFS manual em Python (graph_retriever.py) por Cypher
    nativo, incluindo `shortestPath`, que o Neo4j resolve no próprio banco
    em vez de percorrer arestas em memória no processo do agente."""

    def __init__(self, builder: Neo4jKnowledgeGraphBuilder):
        self.builder = builder

    def get_neighbors(self, entity: str) -> List[dict]:
        query = """
        MATCH (e:Entity {name: $entity})-[r:RELATES_TO]-(n:Entity)
        RETURN n.name AS entity, r.relation AS relation,
               CASE WHEN startNode(r) = e THEN 'out' ELSE 'in' END AS direction
        """
        with self.builder._driver.session() as session:
            result = session.run(query, entity=entity)
            return [dict(record) for record in result]

    def find_path(self, start: str, end: str, max_hops: int = 3) -> List[str]:
        query = f"""
        MATCH (a:Entity {{name: $start}}), (b:Entity {{name: $end}}),
              p = shortestPath((a)-[:RELATES_TO*..{max_hops}]-(b))
        RETURN [n IN nodes(p) | n.name] AS path
        """
        with self.builder._driver.session() as session:
            record = session.run(query, start=start, end=end).single()
            return record["path"] if record else []

    def search(self, query: str) -> List[dict]:
        cypher = """
        MATCH (e:Entity)
        WHERE toLower(e.name) CONTAINS toLower($query)
        RETURN e.name AS name, e.type AS type
        """
        with self.builder._driver.session() as session:
            result = session.run(cypher, query=query)
            return [dict(record) for record in result]

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
