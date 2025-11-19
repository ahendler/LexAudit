from __future__ import annotations
from lexaudit.core.llm_config import create_llm
from lexaudit.prompts.identification import IDENTIFICATION_PROMPT
from lexaudit.prompts.review import REVIEW_PROMPT
from lexaudit.core.models import IdentifiedCitations

from typing import Any, Dict, Optional
import logging

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.language_models.chat_models import BaseChatModel


class StructuredLLM:
    def __init__(
        self,
        *,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        chat_model: Optional[BaseChatModel] = None,
    ) -> None:
        if chat_model is not None:
            self.llm = chat_model
            resolved_name = model_name or getattr(chat_model, "model_name", "custom")
        else:
            self.llm = create_llm(model_name=model_name, temperature=temperature)
            resolved_name = (
                model_name or getattr(self.llm, "model_name", "default")
                if self.llm
                else "unconfigured"
            )
        self.model_name = resolved_name
        logger.info(
            "Initialized chat model class=%s model_name=%s available=%s",
            type(self.llm).__name__ if self.llm else None,
            self.model_name,
            self.llm is not None,
        )

    @property
    def available(self) -> bool:
        return self.llm is not None

    def chain(self, prompt, schema_model):
        if not self.llm:
            return None
        if hasattr(self.llm, "with_structured_output"):
            try:
                return prompt | self.llm.with_structured_output(schema_model)
            except Exception:
                return None
        return None

    def invoke(self, prompt, values: Dict[str, Any], schema_model):
        if not self.llm:
            raise RuntimeError("LLM not configured")
        ch = self.chain(prompt, schema_model)
        if ch is not None:
            logger.info(
                "Invoking structured chain (model=%s) with keys=%s",
                self.model_name,
                list(values.keys()),
            )
            result = ch.invoke(values)
            try:
                logger.info(
                    "Structured output: %s",
                    result.model_dump_json(ensure_ascii=False),
                )
            except Exception:
                logger.debug("[LLM] Structured output parsed")
            return result
        # Fallback
        messages = prompt.format_messages(**values)
        logger.info(
            "Invoking fallback chain (model=%s) with keys=%s",
            self.model_name,
            list(values.keys()),
        )
        response = self.llm.invoke(messages)
        try:
            logger.info("Raw response: %s", getattr(response, "content", ""))
        except Exception:
            logger.debug("Received response")
        parser = JsonOutputParser(pydantic_object=schema_model)
        parsed = parser.parse(response.content)
        return schema_model.model_validate(parsed)


class IdentifierLLM:
    def __init__(
        self,
        *,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> None:
        self._core = StructuredLLM(model_name=model_name, temperature=temperature)
        self.llm = self._core.llm
        self.model_name = self._core.model_name

        # Cadeias LCEL quando suportado
        self.identify_chain = self._core.chain(
            IDENTIFICATION_PROMPT, IdentifiedCitations
        )
        self.review_chain = self._core.chain(REVIEW_PROMPT, IdentifiedCitations)

    @property
    def available(self) -> bool:
        return self._core.available

    # Identificação única
    def identify(self, context_snippet: str) -> IdentifiedCitations:
        values = {"context_snippet": context_snippet}
        return self._core.invoke(IDENTIFICATION_PROMPT, values, IdentifiedCitations)

    # Revisão única
    def review(self, context_snippet: str, proposals_json: str) -> IdentifiedCitations:
        values = {"context_snippet": context_snippet, "proposals_json": proposals_json}
        return self._core.invoke(REVIEW_PROMPT, values, IdentifiedCitations)


__all__ = ["StructuredLLM", "IdentifierLLM"]
logger = logging.getLogger(__name__)
