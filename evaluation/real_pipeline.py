"""
Pipeline real de geração de respostas para o golden-set (`evaluation/golden_dataset.py`).

Dois modos, sempre deixados explícitos no relatório final — nunca se finge
que um rodou quando foi o outro:

- modo "llm" (padrão, usa OPENAI_API_KEY de core.config): recupera contexto
  real via `TfidfRetriever` e gera a resposta com uma chamada real à API da
  OpenAI (sem mock). É o único modo em que os números de RAGAS/DeepEval são
  um julgamento de LLM de verdade.
- modo "offline" (fallback sem rede/sem chave): resposta extrativa
  determinística = o chunk mais bem ranqueado pelo TF-IDF, truncado. Serve
  para o pipeline rodar fim-a-fim (incluindo testes/CI) sem depender de rede,
  mas as métricas resultantes são rotuladas como degradadas no relatório —
  nunca reportadas como avaliação real de LLM.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List

from core.config import OPENAI_API_KEY
from evaluation.golden_dataset import GOLDEN_SET, load_corpus_text
from evaluation.tfidf_retriever import TfidfRetriever, chunk_text

SYSTEM_PROMPT = (
    "Você é o assistente de documentação do projeto OmniMind AI OS. "
    "Responda à pergunta usando SOMENTE as informações do contexto fornecido. "
    "Se o contexto não tiver a resposta, diga que não sabe. Seja direto e "
    "responda em português, em no máximo 3 frases."
)


@dataclass
class EvalRecord:
    question: str
    ground_truth: str
    contexts: List[str]
    answer: str
    latency_ms: float
    mode: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    model: str = ""


def build_retriever(chunk_size: int = 800, overlap: int = 150) -> TfidfRetriever:
    corpus_text = load_corpus_text()
    chunks = chunk_text(corpus_text, chunk_size=chunk_size, overlap=overlap)
    return TfidfRetriever(documents=chunks)


def _answer_offline(contexts: List[str]) -> str:
    if not contexts:
        return "Não sei — nenhum contexto relevante foi recuperado."
    return contexts[0][:300]


def _answer_openai(question: str, contexts: List[str], model: str) -> tuple[str, int, int]:
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)
    context_block = "\n---\n".join(contexts) if contexts else "(sem contexto recuperado)"
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Contexto:\n{context_block}\n\nPergunta: {question}",
            },
        ],
    )
    answer = response.choices[0].message.content or ""
    usage = response.usage
    prompt_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
    completion_tokens = getattr(usage, "completion_tokens", 0) if usage else 0
    return answer.strip(), prompt_tokens, completion_tokens


def generate_eval_records(
    model: str = "gpt-4o-mini",
    k: int = 3,
    force_offline: bool = False,
) -> List[EvalRecord]:
    """Gera contexto (TF-IDF real) + resposta (LLM real ou fallback offline)
    para cada item do golden-set. Retorna sempre registros reais — nunca
    pré-computados/fixos — mas o modo é determinístico (offline) ou
    reprodutível em espírito, não byte-a-byte (llm, por natureza do provedor)."""
    retriever = build_retriever()
    use_llm = bool(OPENAI_API_KEY) and not force_offline

    records: List[EvalRecord] = []
    for item in GOLDEN_SET:
        contexts = retriever.search(item.question, k=k)
        t0 = time.time()
        if use_llm:
            try:
                answer, pt, ct = _answer_openai(item.question, contexts, model=model)
                mode = "llm"
            except Exception as exc:  # rede indisponível, cota excedida, etc.
                answer = f"[erro ao chamar OpenAI: {exc}] " + _answer_offline(contexts)
                pt, ct = 0, 0
                mode = "llm_error_fallback_offline"
        else:
            answer = _answer_offline(contexts)
            pt, ct = 0, 0
            mode = "offline"
        latency_ms = round((time.time() - t0) * 1000, 2)

        records.append(
            EvalRecord(
                question=item.question,
                ground_truth=item.ground_truth,
                contexts=contexts,
                answer=answer,
                latency_ms=latency_ms,
                mode=mode,
                prompt_tokens=pt,
                completion_tokens=ct,
                model=model if use_llm else "offline-extractive",
            )
        )
    return records
