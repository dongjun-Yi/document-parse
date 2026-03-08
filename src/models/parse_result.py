from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ParsedElement:

    category: str
    content: str
    page: int
    coordinates: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParseResult:

    source_filename: str
    elements: list[ParsedElement]
    elapsed_seconds: float
    raw_output: str = ""

    def filter_by_category(self, category: str) -> list[ParsedElement]:
        return [el for el in self.elements if el.category == category]

    @property
    def total_element_count(self) -> int:
        return len(self.elements)

    @property
    def page_count(self) -> int:
        if not self.elements:
            return 0
        return max(el.page for el in self.elements)
