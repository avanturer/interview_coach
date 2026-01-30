"""Абстракция LLM-провайдера."""

from langchain_core.language_models import BaseChatModel
from langchain_mistralai import ChatMistralAI
from langchain_openai import ChatOpenAI

from src.config import settings


def get_llm(
    provider: str | None = None,
    model: str | None = None,
    temperature: float = 0.7,
) -> BaseChatModel:
    """Получить экземпляр LLM для настроенного провайдера."""
    provider = provider or settings.llm_provider
    model = model or settings.llm_model

    if provider == "mistral":
        if not settings.mistral_api_key:
            raise ValueError("MISTRAL_API_KEY не задан")
        return ChatMistralAI(
            model=model,
            api_key=settings.mistral_api_key,
            temperature=temperature,
        )

    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY не задан")
        return ChatOpenAI(
            model=model,
            api_key=settings.openai_api_key,
            temperature=temperature,
        )

    raise ValueError(f"Неизвестный провайдер: {provider}. Поддерживаются: mistral, openai")


def get_llm_for_agent(agent_type: str, temperature: float | None = None) -> BaseChatModel:
    """Получить LLM с настройками температуры для конкретного агента."""
    temps = {
        "interviewer": settings.temp_interviewer,
        "observer": settings.temp_observer,
        "evaluator": settings.temp_evaluator,
    }
    return get_llm(temperature=temperature or temps.get(agent_type, 0.7))
