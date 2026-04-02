"""Extrai entidades nomeadas de texto usando NLP."""
from typing import List, Dict
from agents._llm_factory import get_llm


def extract_with_spacy(text: str) -> List[Dict]:
    """Extração com spaCy (se instalado)."""
    try:
        import spacy
        nlp = spacy.load("pt_core_news_sm")
        doc = nlp(text)
        return [{"text": ent.text, "label": ent.label_, "start": ent.start_char, "end": ent.end_char}
                for ent in doc.ents]
    except Exception:
        return []


class EntityExtractor:
    def __init__(self, provider: str = "ollama", model: str = "mistral"):
        self.llm = get_llm(provider, model)

    def extract(self, text: str) -> List[Dict]:
        """Extrai entidades usando LLM como fallback."""
        spacy_result = extract_with_spacy(text)
        if spacy_result:
            return spacy_result
        # Fallback: extração via LLM
        prompt = (
            f"Extraia todas as entidades do texto abaixo. "
            f"Para cada entidade, informe: nome, tipo (pessoa, lugar, organização, data, produto).\n"
            f"Formato: NOME | TIPO\n\nTexto: {text}"
        )
        response = self.llm.invoke(prompt).content.strip()
        entities = []
        for line in response.split("\n"):
            if "|" in line:
                parts = line.split("|")
                if len(parts) >= 2:
                    entities.append({"text": parts[0].strip(), "label": parts[1].strip()})
        return entities
