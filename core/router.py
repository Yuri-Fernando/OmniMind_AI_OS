"""
Roteador de perguntas: decide qual agente especializado deve processar a query.
"""


def route_question(state: dict) -> str:
    """
    Analisa a question no estado e retorna o nó destino no grafo.

    Retorna:
        'rag'   - perguntas sobre documentos/knowledge base
        'tool'  - perguntas que precisam de ferramentas externas
        'exec'  - perguntas genéricas / conversação
    """
    question = state.get("question", "").lower()

    tool_keywords = [
        "clima", "weather", "temperatura", "calcul", "compute",
        "buscar", "search", "pesquisar", "scrape", "executar código",
        "run code", "execute",
    ]
    doc_keywords = [
        "documento", "pdf", "arquivo", "texto", "contexto",
        "segundo o", "de acordo com", "baseado em",
    ]

    if any(kw in question for kw in tool_keywords):
        return "tool"
    if any(kw in question for kw in doc_keywords):
        return "rag"
    return "rag"
