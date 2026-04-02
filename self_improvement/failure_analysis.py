"""Análise de falhas: identifica padrões e causas raiz de erros."""
import json, os
from collections import Counter
from typing import List
from agents._llm_factory import get_llm


class FailureAnalyzer:
    def __init__(self, provider: str = "ollama", model: str = "mistral",
                 log_path: str = "data/failures.json"):
        self.llm = get_llm(provider, model)
        self.log_path = log_path
        self.failures: List[dict] = []
        self._load()

    def log(self, task: str, error: str, context: str = ""):
        import time
        self.failures.append({"task": task, "error": error, "context": context, "ts": time.time()})
        self._save()

    def analyze(self, last_n: int = 10) -> dict:
        recent = self.failures[-last_n:]
        if not recent:
            return {"message": "Nenhuma falha registrada."}
        errors = [f["error"] for f in recent]
        error_counts = Counter(e.split(":")[0] for e in errors)
        context = "\n".join(f"- Tarefa: {f['task']}\n  Erro: {f['error']}" for f in recent)
        prompt = (
            f"Analise os erros abaixo e identifique os padrões mais comuns e causas raiz.\n\n{context}\n\n"
            f"Forneça um resumo e recomendações de melhoria."
        )
        analysis = self.llm.invoke(prompt).content.strip()
        return {"recent_failures": len(recent), "error_types": dict(error_counts), "analysis": analysis}

    def _save(self):
        os.makedirs(os.path.dirname(self.log_path) or ".", exist_ok=True)
        with open(self.log_path, "w") as f:
            json.dump(self.failures, f, indent=2)

    def _load(self):
        if os.path.exists(self.log_path):
            with open(self.log_path) as f:
                self.failures = json.load(f)
