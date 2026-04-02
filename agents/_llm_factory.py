"""
Factory de LLMs — retorna instâncias LangChain compatíveis para qualquer provedor.
Suporta: OpenAI, Anthropic, Ollama (local).
"""
from core.config import OPENAI_API_KEY, ANTHROPIC_API_KEY, OLLAMA_BASE_URL


def get_llm(provider: str = "openai", model: str = "gpt-4o-mini"):
    """
    Retorna uma instância LangChain LLM para o provedor/modelo escolhido.

    Args:
        provider: 'openai' | 'anthropic' | 'ollama'
        model: nome do modelo

    Returns:
        Instância de BaseChatModel compatível com .invoke()
    """
    provider = provider.lower()

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model, api_key=OPENAI_API_KEY or None)

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model, api_key=ANTHROPIC_API_KEY or None)

    if provider == "ollama":
        from langchain_community.chat_models import ChatOllama
        return ChatOllama(model=model, base_url=OLLAMA_BASE_URL)

    raise ValueError(f"Provedor desconhecido: '{provider}'. Use 'openai', 'anthropic' ou 'ollama'.")
