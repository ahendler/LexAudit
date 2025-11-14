from __future__ import annotations

import os
import shlex
import shutil
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

load_dotenv()

class LexAuditSettings(BaseSettings):

    linker_cmd: str = "docker run -i --rm lexmlbr/lexml-linker:latest /usr/bin/linkertool"
    linker_context: str = "federal"
    dedup_gap_l2: int = 8
    linker_timeout: Optional[float] = 1.0

    llm_provider: str = "openai"
    llm_model: str = "gpt-5-nano"
    llm_temperature: float = 0.0

    serpapi_api_key: str = ""
    google_api_key: str = ""
    openai_api_key: str = ""



SETTINGS = LexAuditSettings()

