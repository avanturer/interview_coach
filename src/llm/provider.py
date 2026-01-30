"""LLM provider abstraction."""

from langchain_core.language_models import BaseChatModel
from langchain_mistralai import ChatMistralAI
from langchain_openai import ChatOpenAI

from src.config import settings


def get_llm(
    provider: str | None = None,
    model: str | None = None,
    temperature: float = 0.7,
) -> BaseChatModel:
    """Get LLM instance for the configured provider."""
    provider = provider or settings.llm_provider
    model = model or settings.llm_model

    if provider == "mistral":
        if not settings.mistral_api_key:
            raise ValueError("MISTRAL_API_KEY is required")
        return ChatMistralAI(
            model=model,
            api_key=settings.mistral_api_key,
            temperature=temperature,
        )

    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required")
        return ChatOpenAI(
            model=model,
            api_key=settings.openai_api_key,
            temperature=temperature,
        )

    raise ValueError(f"Unknown provider: {provider}. Supported: mistral, openai")


def get_llm_for_agent(agent_type: str, temperature: float | None = None) -> BaseChatModel:
    """Get LLM with agent-specific temperature settings."""
    temps = {"interviewer": 0.7, "observer": 0.3, "evaluator": 0.5}
    return get_llm(temperature=temperature or temps.get(agent_type, 0.7))
