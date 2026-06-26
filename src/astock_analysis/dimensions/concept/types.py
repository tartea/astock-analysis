"""Type definitions for concept board dimension responses."""

from __future__ import annotations

from typing import TypedDict


class ConceptResponse(TypedDict):
    """Concept board data response."""

    data: list[dict]
    provider: str
    board_name: str
