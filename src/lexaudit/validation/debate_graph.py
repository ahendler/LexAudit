"""
Multi-agent debate graph for complex citation validation.
"""

import logging
from typing import Any, Dict, List, TypedDict
from pydantic import BaseModel, Field

from langgraph.graph import StateGraph, END

from ..core.structured_llm import StructuredLLM
from ..core.models import CitationRetrieval
from ..prompts.validation import VERIFIER_PROMPT, MODERATOR_PROMPT

logger = logging.getLogger(__name__)


class VerifierArgument(BaseModel):
    """Argument from a verifier agent."""

    agent_id: str
    position: str
    confidence: float = Field(ge=0.0, le=1.0)
    argument: str
    counterarguments: str = ""


class ModeratorDecision(BaseModel):
    """Final decision from moderator."""

    validation_status: str
    confidence: float = Field(ge=0.0, le=1.0)
    justification: str
    consensus_level: str


class DebateState(TypedDict):
    """State for the debate graph."""

    citation_retrieval: CitationRetrieval
    citation_context: str
    citation_reference: str
    official_text: str
    extracted_section: str
    verifier_arguments: List[Dict[str, Any]]
    current_round: int
    final_decision: Dict[str, Any]


class DebateGraph:
    """
    Multi-agent debate graph for complex citation validation.
    """

    VERIFIER_PERSPECTIVES = [
        "Verificação de Correspondência Textual: Analise se o texto citado corresponde exatamente ao texto oficial, considerando sinônimos e paráfrases.",
        "Verificação de Validade Temporal: Analise se a norma está vigente, revogada ou alterada, procurando por marcadores de revogação.",
        "Verificação de Interpretação Jurídica: Analise se a interpretação ou inferência feita no documento está compatível com o texto oficial.",
    ]

    def __init__(self):
        """Initialize debate graph."""
        self.llm = StructuredLLM()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine."""
        workflow = StateGraph(DebateState)

        workflow.add_node("verifier_0", self._verifier_node_0)
        workflow.add_node("verifier_1", self._verifier_node_1)
        workflow.add_node("verifier_2", self._verifier_node_2)
        workflow.add_node("moderator", self._moderator_node)

        workflow.set_entry_point("verifier_0")

        workflow.add_edge("verifier_0", "verifier_1")
        workflow.add_edge("verifier_1", "verifier_2")
        workflow.add_edge("verifier_2", "moderator")
        workflow.add_edge("moderator", END)

        return workflow.compile()

    def _verifier_node_0(self, state: DebateState) -> Dict[str, Any]:
        """First verifier agent."""
        return self._verifier_node(state, 0)

    def _verifier_node_1(self, state: DebateState) -> Dict[str, Any]:
        """Second verifier agent."""
        return self._verifier_node(state, 1)

    def _verifier_node_2(self, state: DebateState) -> Dict[str, Any]:
        """Third verifier agent."""
        return self._verifier_node(state, 2)

    def _verifier_node(self, state: DebateState, agent_idx: int) -> Dict[str, Any]:
        """
        Generic verifier agent node.

        Args:
            state: Current debate state
            agent_idx: Index of the verifier agent (0-2)

        Returns:
            Updated state with new argument
        """
        agent_id = f"verifier_{agent_idx}"
        perspective = self.VERIFIER_PERSPECTIVES[agent_idx]

        previous_arguments = (
            "\n\n".join(
                f"Agente {arg['agent_id']}: {arg['argument']}"
                for arg in state["verifier_arguments"]
            )
            or "Nenhum argumento anterior."
        )

        values = {
            "perspective": perspective,
            "agent_id": agent_id,
            "citation_context": state["citation_context"],
            "citation_reference": state["citation_reference"],
            "official_text": state["official_text"],
            "extracted_section": state["extracted_section"],
            "previous_arguments": previous_arguments,
        }

        logger.info("  [DEBATE] %s analyzing...", agent_id)

        argument = self.llm.invoke(VERIFIER_PROMPT, values, VerifierArgument)

        logger.info(
            "    -> Position: %s (confidence=%.2f)",
            argument.position,
            argument.confidence,
        )

        state["verifier_arguments"].append(argument.model_dump())

        return state

    def _moderator_node(self, state: DebateState) -> Dict[str, Any]:
        """
        Moderator agent that synthesizes the debate.

        Args:
            state: Current debate state with all verifier arguments

        Returns:
            Updated state with final decision
        """
        all_arguments = "\n\n---\n\n".join(
            f"Agente {arg['agent_id']} ({arg['position']}, confiança {arg['confidence']}):\n"
            f"Argumento: {arg['argument']}\n"
            f"Contra-argumentos: {arg['counterarguments']}"
            for arg in state["verifier_arguments"]
        )

        values = {
            "citation_context": state["citation_context"],
            "citation_reference": state["citation_reference"],
            "official_text": state["official_text"],
            "extracted_section": state["extracted_section"],
            "all_arguments": all_arguments,
        }

        logger.info("  [DEBATE] Moderator synthesizing...")

        decision = self.llm.invoke(MODERATOR_PROMPT, values, ModeratorDecision)

        logger.info(
            "    -> Final decision: %s (confidence=%.2f, consensus=%s)",
            decision.validation_status,
            decision.confidence,
            decision.consensus_level,
        )

        final_decision = decision.model_dump()
        final_decision["verifier_arguments"] = state["verifier_arguments"]

        state["final_decision"] = final_decision

        return state

    def run_debate(self, citation_retrieval: CitationRetrieval) -> Dict[str, Any]:
        """
        Run multi-agent debate for a citation.

        Args:
            citation_retrieval: Citation with retrieved document

        Returns:
            Final decision with validation_status, confidence, and justification

        Raises:
            Exception: If debate fails (intentional crash)
        """
        resolved = citation_retrieval.resolved_citation
        retrieved_doc = citation_retrieval.retrieved_document
        extracted_citation = resolved.extracted_citation

        initial_state: DebateState = {
            "citation_retrieval": citation_retrieval,
            "citation_context": extracted_citation.context_snippet or "",
            "citation_reference": extracted_citation.formatted_name,
            "official_text": (
                retrieved_doc.full_text[:5000]
                if retrieved_doc
                else "DOCUMENTO NÃO RECUPERADO"
            ),
            "extracted_section": (
                retrieved_doc.metadata.get("extracted_text", "Não disponível")
                if retrieved_doc
                else "Não disponível"
            ),
            "verifier_arguments": [],
            "current_round": 0,
            "final_decision": {},
        }

        logger.info(
            "Starting multi-agent debate for: %s", initial_state["citation_reference"]
        )

        final_state = self.graph.invoke(initial_state)

        return final_state["final_decision"]
