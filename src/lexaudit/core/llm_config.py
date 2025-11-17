"""
LLM configuration and factory for creating LangChain chat models.
"""
import os
from typing import Optional
from langchain_core.language_models.chat_models import BaseChatModel
from config.settings import SETTINGS


def create_llm(
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
    temperature: Optional[float] = None
) -> Optional[BaseChatModel]:
    """
    Create a LangChain chat model based on provider configuration.

    Args:
        provider: LLM provider (openai, google, gemini, anthropic, ollama).
                  Reads from LLM_PROVIDER env if not provided.
        model_name: Model name. Reads from LLM_MODEL env if not provided.
        temperature: Temperature. Reads from LLM_TEMPERATURE env if not provided.

    Returns:
        Configured LangChain chat model, or None if configuration fails.
    """
    provider = provider or SETTINGS.llm_provider
    model_name = model_name or SETTINGS.llm_model
    temperature = temperature if temperature is not None else SETTINGS.llm_temperature

    try:
        if provider == "openai":
            from langchain_openai import ChatOpenAI
            api_key = SETTINGS.openai_api_key
            if not api_key:
                print(f"[LLM_CONFIG] Warning: openai_api_key not set")
                return None
            return ChatOpenAI(model=model_name, temperature=temperature, api_key=api_key)

        elif provider in ["google", "gemini"]:
            from langchain_google_genai import ChatGoogleGenerativeAI
            api_key = SETTINGS.google_api_key
            if not api_key:
                print(f"[LLM_CONFIG] Warning: google_api_key not set")
                return None
            return ChatGoogleGenerativeAI(model=model_name, temperature=temperature, google_api_key=api_key)

        elif provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                print(f"[LLM_CONFIG] Warning: ANTHROPIC_API_KEY not set")
                return None
            return ChatAnthropic(model=model_name, temperature=temperature, api_key=api_key)

        elif provider == "ollama":
            from langchain_community.chat_models import ChatOllama
            return ChatOllama(model=model_name, temperature=temperature)

        else:
            print(f"[LLM_CONFIG] Warning: Unknown provider '{provider}'")
            return None

    except ImportError as e:
        print(f"[LLM_CONFIG] Warning: Could not import {provider} client: {e}")
        print(f"[LLM_CONFIG] Install with: pip install langchain-{provider}")
        return None
