from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# ParsedElement
# ---------------------------------------------------------------------------


@dataclass
class ParsedElement:
    """A single content element extracted from a document.

    Attributes:
        category:    Element type, e.g. 'paragraph', 'table', 'figure', 'equation'.
        content:     Extracted text or HTML content.
        page:        1-based page number where the element was found.
        coordinates: Bounding box coordinates from the API (optional).
        metadata:    Any additional metadata returned by the API.
    """

    category: str
    content: str
    page: int
    coordinates: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# ParseResult
# ---------------------------------------------------------------------------


@dataclass
class ParseResult:
    """Aggregated result of parsing a single document.

    Attributes:
        source_filename: Original file name that was parsed.
        elements:        List of all extracted elements.
        elapsed_seconds: Total time taken for the API call (in seconds).
        raw_output:      Full raw HTML/text response from the API.
    """

    source_filename: str
    elements: list[ParsedElement]
    elapsed_seconds: float
    raw_output: str = ""

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def filter_by_category(self, category: str) -> list[ParsedElement]:
        """Return only elements matching the given category."""
        return [el for el in self.elements if el.category == category]

    @property
    def total_element_count(self) -> int:
        return len(self.elements)

    @property
    def page_count(self) -> int:
        if not self.elements:
            return 0
        return max(el.page for el in self.elements)
