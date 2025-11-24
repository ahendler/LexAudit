from langchain_core.embeddings import Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import OpenAIEmbeddings

from lexaudit.config.settings import SETTINGS


def get_embeddings() -> Embeddings:
    """
    Factory to create embeddings based on settings.

    Returns:
        Embeddings: Configured embeddings instance.

    Raises:
        ValueError: If the provider is not supported.
    """
    provider = SETTINGS.embedding_provider.lower()

    if provider == "gemini":
        return GoogleGenerativeAIEmbeddings(
            model=SETTINGS.embedding_model, google_api_key=SETTINGS.google_api_key
        )
    elif provider == "openai":
        return OpenAIEmbeddings(
            model=SETTINGS.embedding_model, openai_api_key=SETTINGS.openai_api_key
        )
    else:
        raise ValueError(f"Unsupported embedding provider: {provider}")
