# GraphRAG (`rag/graph_rag.py`)

Composição real de duas capacidades que o projeto já tinha separadas:

```text
                 documento
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
  rag/ (Chroma +            knowledge_graph/
  embeddings)                (EntityExtractor + KnowledgeGraphBuilder)
        │                         │
   chunk + embedding      entidades + relações (LLM)
        │                         │
        └────────────┬────────────┘
                     ▼
              GraphRAGPipeline.ingest()


                   query
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
  vector_store.search()    entidades da query
  (similaridade)                  │
        │                  GraphRetriever.get_neighbors()
        │                  (travessia do grafo)
        └────────────┬────────────┘
                     ▼
              GraphRAGContext.render()
                     │
                     ▼
                 prompt do LLM
```

## Por que não é só RAG + "grafo" no nome

Busca vetorial responde bem a perguntas **factuais/semânticas** ("o que é
X"). Ela falha em perguntas **relacionais** ("onde X trabalhou", "quem X
colaborou com") quando as duas entidades relacionadas não são textualmente
parecidas — "Marie Curie" e "Sorbonne" não compartilham palavras, então um
chunk sobre a Sorbonne pode nunca aparecer no top-k por similaridade.

O grafo tem a aresta `trabalhou_em -> Sorbonne` direto. `GraphRAGPipeline`
soma os dois sinais em vez de depender só de um — ver
`rag/tests/test_graph_rag.py::test_graph_context_surfaces_relation_vector_search_would_miss`,
que reproduz exatamente esse caso.

## API

```python
from memory.vector_memory import VectorMemory
from rag.graph_rag import GraphRAGPipeline

pipeline = GraphRAGPipeline(vector_store=VectorMemory())
pipeline.ingest("Marie Curie trabalhou com Pierre Curie na Sorbonne.", source="bio.txt")

context = pipeline.retrieve("Onde Marie Curie trabalhou?")
print(context.render())          # pronto para entrar no prompt do LLM
print(pipeline.stats())          # {'nodes': ..., 'edges': ..., 'vector_store': 'VectorMemory'}
```

`vector_store` aceita qualquer objeto com `.store(text, metadata)` /
`.search(query, k)` — `memory/vector_memory.py::VectorMemory` (Chroma) já
implementa essa interface. `kg_builder`/`entity_extractor` são injetáveis
(usados pelos testes com fakes, sem depender de um provedor de LLM rodando).

## Testes

5 testes (`rag/tests/test_graph_rag.py`) com fakes de vector store e grafo
— exercitam a lógica real de composição sem precisar de Chroma nem de LLM
rodando. `notebooks/graph_rag_demo.ipynb` usa o pipeline real (Chroma +
`EntityExtractor`, requer um provedor de LLM configurado — Ollama local por
padrão).
