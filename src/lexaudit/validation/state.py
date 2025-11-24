"""
LangGraph state definition for validation workflow.
"""

import operator
from typing import Annotated, List, Optional, TypedDict

from ..core.models import AgentArgument, CitationRetrieval, TriageDecision, ValidatedCitation


class ValidationState(TypedDict):
    """State for the validation graph workflow."""

    # Input
    citation_retrieval: CitationRetrieval

    # Triage output
    triage_result: Optional[TriageDecision]

    # Discussion accumulator
    discussion_history: Annotated[List[AgentArgument], operator.add]

    # Round counter for debate
    round_counter: int

    # Final output
    final_validation: Optional[ValidatedCitation]
