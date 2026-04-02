"""Motor de raciocínio: seleciona e executa a estratégia mais adequada."""
from reasoning.chain_of_thought import ChainOfThought
from reasoning.tree_of_thoughts import TreeOfThoughts


class ReasoningEngine:
    STRATEGIES = {"cot", "tot", "direct"}

    def __init__(self, provider: str = "ollama", model: str = "mistral"):
        self.provider = provider
        self.model = model
        self._cot = None
        self._tot = None

    @property
    def cot(self) -> ChainOfThought:
        if not self._cot:
            self._cot = ChainOfThought(self.provider, self.model)
        return self._cot

    @property
    def tot(self) -> TreeOfThoughts:
        if not self._tot:
            self._tot = TreeOfThoughts(self.provider, self.model)
        return self._tot

    def _select_strategy(self, question: str) -> str:
        q = question.lower()
        if any(w in q for w in ["passo", "etapa", "como", "explique", "calcule"]):
            return "cot"
        if any(w in q for w in ["melhor", "opção", "compare", "analise", "estratégia"]):
            return "tot"
        return "direct"

    def reason(self, question: str, strategy: str = "auto") -> dict:
        if strategy == "auto":
            strategy = self._select_strategy(question)

        if strategy == "cot":
            result = self.cot.reason(question)
            result["strategy"] = "chain_of_thought"
        elif strategy == "tot":
            result = self.tot.solve(question)
            result["strategy"] = "tree_of_thoughts"
        else:
            from agents._llm_factory import get_llm
            llm = get_llm(self.provider, self.model)
            answer = llm.invoke(question).content
            result = {"question": question, "answer": answer, "strategy": "direct"}

        return result
