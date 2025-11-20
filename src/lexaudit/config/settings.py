from __future__ import annotations

from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv(Path(__file__).parent.parent.parent.parent / "config" / ".env")


class LexAuditSettings(BaseSettings):
    linker_cmd: str = (
        "docker run -i --rm lexmlbr/lexml-linker:latest /usr/bin/linkertool"
    )
    linker_context: str = "federal"
    linker_timeout: Optional[float] = 1.0

    # Snippet generation defaults
    snippet_min_chars: int = 120
    snippet_max_chars: Optional[int] = 600
    prefer_linker_edges: bool = True

    llm_provider: str = "gemini"
    llm_model: str = "gemini-2.5-flash"
    llm_temperature: float = 0.0

    serpapi_api_key: str = ""
    google_api_key: str = ""
    openai_api_key: str = ""
    # Logging
    logging_level: str = "INFO"


SETTINGS = LexAuditSettings()
