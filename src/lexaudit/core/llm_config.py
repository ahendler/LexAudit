"""
LLM configuration and factory for creating LangChain chat models.
"""
import os
from typing import Optional
from langchain_core.language_models.chat_models import BaseChatModel


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
    provider = provider or os.getenv("LLM_PROVIDER", "openai").lower()
    model_name = model_name or os.getenv("LLM_MODEL", "gpt-4o-mini")
    temperature = temperature if temperature is not None else float(
        os.getenv("LLM_TEMPERATURE", "0"))

    try:
        if provider == "openai":
            from langchain_openai import ChatOpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print(f"[LLM_CONFIG] Warning: OPENAI_API_KEY not set")
                return None
            return ChatOpenAI(model=model_name, temperature=temperature, api_key=api_key)

        elif provider in ["google", "gemini"]:
            from langchain_google_genai import ChatGoogleGenerativeAI
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                print(f"[LLM_CONFIG] Warning: GOOGLE_API_KEY not set")
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
