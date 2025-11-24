"""
LangGraph workflow for multi-agent validation.
"""

import logging
from typing import Any, Dict, Literal

from langchain_core.output_parsers import JsonOutputParser
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import create_react_agent

from ..config.settings import SETTINGS
from ..core.llm_config import create_llm
from ..core.models import (
    AgentArgument,
    TriageDecision,
    ValidatedCitation,
    ValidationStatus,
)
from ..indexing.document_index import LegalDocumentIndex
from ..prompts.validation import (
    ADVOCATE_PROMPT,
    SKEPTIC_PROMPT,
    SYNTHESIZER_PROMPT,
    TRIAGE_PROMPT,
)
from .state import ValidationState
from .tools import create_query_tool

logger = logging.getLogger(__name__)


def build_validation_graph(indexer: LegalDocumentIndex):
    """
    Build the LangGraph workflow for citation validation.

    Args:
        indexer: The LegalDocumentIndex for querying documents

    Returns:
        Compiled LangGraph workflow
    """
    # Create LLM
    llm = create_llm()

    # Create tool
    query_tool = create_query_tool(indexer)

    # Define nodes

    def triage_node(state: ValidationState) -> Dict[str, Any]:
        """Triage agent decides if citation needs discussion."""
        logger.info("Analyzing citation...")

        retrieval = state["citation_retrieval"]
        resolved = retrieval.resolved_citation
        extracted = resolved.extracted_citation
        retrieved_doc = retrieval.retrieved_document

        # Handle missing document immediately
        if retrieval.retrieval_status != "success" or not retrieved_doc:
            logger.info("  -> Document not retrieved, marking as NON_EXISTENT")
            decision = TriageDecision(
                needs_discussion=False,
                confidence=1.0,
                preliminary_status=ValidationStatus.NON_EXISTENT,
                reasoning=(
                    f"Documento oficial não foi recuperado. "
                    f"Status de recuperação: {retrieval.retrieval_status}"
                ),
            )
            return {"triage_result": decision}

        # Create ReAct agent with tool
        agent = create_react_agent(llm, [query_tool])

        # Prepare prompt values
        prompt_values = {
            "identified_string": extracted.identified_string,
            "formatted_name": extracted.formatted_name,
            "citation_type": extracted.citation_type,
            "context_snippet": extracted.context_snippet,
            "canonical_id": resolved.canonical_id or "unknown",
            "retrieval_status": retrieval.retrieval_status,
            "document_title": retrieved_doc.title if retrieved_doc else "N/A",
            "threshold": SETTINGS.validation_confidence_threshold,
        }

        # Format prompt
        messages = TRIAGE_PROMPT.format_messages(**prompt_values)

        # Invoke agent with structured output parsing
        try:
            result = agent.invoke({"messages": messages})
            final_message = result["messages"][-1].content

            # Parse using JsonOutputParser (same pattern as StructuredLLM)
            parser = JsonOutputParser(pydantic_object=TriageDecision)
            decision_dict = parser.parse(final_message)
            decision = TriageDecision(**decision_dict)

            logger.info(
                f"  -> Decision: needs_discussion={decision.needs_discussion}, "
                f"confidence={decision.confidence:.2f}, status={decision.preliminary_status.value}"
            )

            return {"triage_result": decision}

        except Exception as e:
            logger.error(f"Triage agent error: {e}")
            # Fallback: send to discussion
            decision = TriageDecision(
                needs_discussion=True,
                confidence=0.5,
                preliminary_status=ValidationStatus.PENDING,
                reasoning=f"Erro na triagem: {str(e)}. Encaminhando para discussão.",
            )
            return {"triage_result": decision}

    def advocate_node(state: ValidationState) -> Dict[str, Any]:
        """Advocate agent argues citation is correct."""
        logger.info("[Advocate] Building defense...")

        retrieval = state["citation_retrieval"]
        resolved = retrieval.resolved_citation
        extracted = resolved.extracted_citation

        # Create ReAct agent
        agent = create_react_agent(llm, [query_tool])

        # Format discussion history
        discussion_history = "\n\n".join(
            [
                f"**{arg.role.upper()}:** {arg.reasoning}\nEvidências: {arg.evidence_chunks}"
                for arg in state.get("discussion_history", [])
            ]
        )
        if not discussion_history:
            discussion_history = "(Nenhum argumento anterior)"

        prompt_values = {
            "identified_string": extracted.identified_string,
            "context_snippet": extracted.context_snippet,
            "canonical_id": resolved.canonical_id or "unknown",
            "discussion_history": discussion_history,
        }

        messages = ADVOCATE_PROMPT.format_messages(**prompt_values)

        try:
            result = agent.invoke({"messages": messages})
            final_message = result["messages"][-1].content

            # Parse using JsonOutputParser
            parser = JsonOutputParser(pydantic_object=AgentArgument)
            arg_dict = parser.parse(final_message)
            argument = AgentArgument(**arg_dict)
            
            logger.info(f"  -> Argument: {argument.reasoning[:100]}...")

            return {"discussion_history": [argument], "round_counter": state["round_counter"] + 1}

        except Exception as e:
            logger.error(f"Advocate error: {e}")
            # Fallback argument
            argument = AgentArgument(
                role="advocate",
                reasoning=f"Erro ao gerar argumento: {str(e)}",
                evidence_chunks=[],
            )
            return {"discussion_history": [argument], "round_counter": state["round_counter"] + 1}

    def skeptic_node(state: ValidationState) -> Dict[str, Any]:
        """Skeptic agent argues citation has problems."""
        logger.info("[Skeptic] Analyzing for problems...")

        retrieval = state["citation_retrieval"]
        resolved = retrieval.resolved_citation
        extracted = resolved.extracted_citation

        agent = create_react_agent(llm, [query_tool])

        discussion_history = "\n\n".join(
            [
                f"**{arg.role.upper()}:** {arg.reasoning}\nEvidências: {arg.evidence_chunks}"
                for arg in state.get("discussion_history", [])
            ]
        )

        prompt_values = {
            "identified_string": extracted.identified_string,
            "context_snippet": extracted.context_snippet,
            "canonical_id": resolved.canonical_id or "unknown",
            "discussion_history": discussion_history,
        }

        messages = SKEPTIC_PROMPT.format_messages(**prompt_values)

        try:
            result = agent.invoke({"messages": messages})
            final_message = result["messages"][-1].content

            # Parse using JsonOutputParser
            parser = JsonOutputParser(pydantic_object=AgentArgument)
            arg_dict = parser.parse(final_message)
            argument = AgentArgument(**arg_dict)
            
            logger.info(f"  -> Argument: {argument.reasoning[:100]}...")

            return {"discussion_history": [argument]}

        except Exception as e:
            logger.error(f"Skeptic error: {e}")
            argument = AgentArgument(
                role="skeptic",
                reasoning=f"Erro ao gerar argumento: {str(e)}",
                evidence_chunks=[],
            )
            return {"discussion_history": [argument]}

    def synthesizer_node(state: ValidationState) -> Dict[str, Any]:
        """Synthesizer produces final validation."""
        logger.info("[Synthesizer] Producing final verdict...")

        retrieval = state["citation_retrieval"]
        resolved = retrieval.resolved_citation
        extracted = resolved.extracted_citation
        retrieved_doc = retrieval.retrieved_document

        # Format discussion
        discussion_history = "\n\n".join(
            [
                f"**{arg.role.upper()}:** {arg.reasoning}\nEvidências: {arg.evidence_chunks}"
                for arg in state.get("discussion_history", [])
            ]
        )
        if not discussion_history:
            discussion_history = "(Sem discussão - decisão direta da triagem)"

        triage_result = state.get("triage_result")
        triage_reasoning = (
            triage_result.reasoning if triage_result else "Nenhuma decisão preliminar"
        )

        prompt_values = {
            "identified_string": extracted.identified_string,
            "formatted_name": extracted.formatted_name,
            "context_snippet": extracted.context_snippet,
            "canonical_id": resolved.canonical_id or "unknown",
            "retrieval_status": retrieval.retrieval_status,
            "discussion_history": discussion_history,
            "triage_reasoning": triage_reasoning,
        }

        messages = SYNTHESIZER_PROMPT.format_messages(**prompt_values)

        # Use LLM directly (no tools for synthesizer)
        try:
            response = llm.invoke(messages)
            content = response.content

            # Parse using JsonOutputParser - but synthesizer needs special handling
            # because it returns ValidatedCitation fields, not the full object
            if isinstance(content, str):
                # Extract JSON from response
                parser = JsonOutputParser()
                result_dict = parser.parse(content)
            else:
                result_dict = content

            # Create ValidatedCitation
            validated = ValidatedCitation(
                resolved_citation=resolved,
                retrieved_document=retrieved_doc,
                validation_status=ValidationStatus(result_dict["validation_status"]),
                justification=result_dict["justification"],
                confidence=result_dict["confidence"],
                discussion_messages=state.get("discussion_history", []),
            )

            logger.info(
                f"  -> Verdict: {validated.validation_status.value} "
                f"(confidence: {validated.confidence:.2f})"
            )

            return {"final_validation": validated}

        except Exception as e:
            logger.error(f"Synthesizer error: {e}")
            # Fallback validation
            validated = ValidatedCitation(
                resolved_citation=resolved,
                retrieved_document=retrieved_doc,
                validation_status=ValidationStatus.PENDING,
                justification=f"Erro na síntese: {str(e)}",
                confidence=0.0,
                discussion_messages=state.get("discussion_history", []),
            )
            return {"final_validation": validated}

    # Routing functions

    def should_discuss(state: ValidationState) -> Literal["discuss", "synthesize"]:
        """Route based on triage decision."""
        triage_result = state.get("triage_result")
        if triage_result and triage_result.needs_discussion:
            logger.info("  -> Routing to discussion")
            return "discuss"
        else:
            logger.info("  -> Routing directly to synthesis")
            return "synthesize"

    def continue_debate(state: ValidationState) -> Literal["advocate", "synthesize"]:
        """Check if debate should continue."""
        round_counter = state.get("round_counter", 0)
        max_rounds = SETTINGS.debate_rounds * 2  # 2 messages per round (advocate + skeptic)

        if round_counter >= max_rounds:
            logger.info(f"  -> Debate complete ({round_counter} exchanges)")
            return "synthesize"
        else:
            logger.info(f"  -> Continue debate (round {round_counter}/{max_rounds})")
            return "advocate"

    # Build graph
    workflow = StateGraph(ValidationState)

    # Add nodes
    workflow.add_node("triage", triage_node)
    workflow.add_node("advocate", advocate_node)
    workflow.add_node("skeptic", skeptic_node)
    workflow.add_node("synthesizer", synthesizer_node)

    # Set entry point
    workflow.set_entry_point("triage")

    # Add edges
    workflow.add_conditional_edges(
        "triage",
        should_discuss,
        {
            "discuss": "advocate",
            "synthesize": "synthesizer",
        },
    )

    workflow.add_edge("advocate", "skeptic")

    workflow.add_conditional_edges(
        "skeptic",
        continue_debate,
        {
            "advocate": "advocate",
            "synthesize": "synthesizer",
        },
    )

    workflow.add_edge("synthesizer", END)

    # Compile
    compiled = workflow.compile()

    logger.info(" Validation graph compiled successfully")

    return compiled
