"""Structured, grounded answer decisions returned by the answer endpoint."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class GroundedAnswer(BaseModel):
    """A user-facing decision based only on the retrieved evidence or policy."""

    model_config = ConfigDict(extra="forbid")

    decision: Literal["answer", "answer_negative", "answer_partial", "redirect", "refuse"] = Field(
        description=(
            "answer: approved evidence fully answers the question; answer_negative: approved "
            "evidence explicitly says the capability is unsupported or out of scope; "
            "answer_partial: requested information remains unsupported, incomplete, or genuinely "
            "conflicting after explaining documented scoped exceptions; redirect: an evidenced "
            "business policy requires directing the requester "
            "to another response section; refuse: no approved content supports drafting an answer "
            "and the request must be routed to an SME."
        )
    )
    answer: str = Field(description="Concise user-facing answer, policy redirect, or SME-routing statement.")
    citations: list[int] = Field(description="Retrieved chunk IDs that support this decision and answer.")
    needs_sme_review: bool = Field(description="True when evidence is incomplete, missing, or conflicting, or SME input is required.")
    reason: str = Field(description="Short user-facing justification based on supplied evidence or applicable policy.")
