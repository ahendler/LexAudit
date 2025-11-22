"""
Pydantic models for retrieved citation checking.
"""

from pydantic import BaseModel, Field


class RetrievedCitationCheck(BaseModel):
    """Result of checking if retrieved document matches the citation."""

    matches: bool = Field(
        description="Whether the retrieved document matches the citation"
    )
    reasoning: str = Field(description="Explanation of the check decision")
    extracted_text: str = Field(
        default="",
        description="Specific extracted portion (e.g., the cited article) if applicable",
    )
