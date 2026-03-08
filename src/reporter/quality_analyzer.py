from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from html.parser import HTMLParser

from src.models.parse_result import ParsedElement, ParseResult


_TABLE_CATEGORIES = {"table"}
_FIGURE_CATEGORIES = {"figure", "chart"}
_TEXT_CATEGORIES = {
    "paragraph",
    "heading",
    "heading1",
    "heading2",
    "heading3",
    "header",
    "footer",
    "caption",
    "list",
    "list-item",
}


class _TableTagDetector(HTMLParser):

    def __init__(self) -> None:
        super().__init__()
        self.has_td = False

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag == "td":
            self.has_td = True


def _has_valid_table_structure(html: str) -> bool:
    detector = _TableTagDetector()
    detector.feed(html)
    return detector.has_td


@dataclass
class QualityReport:

    source_filename: str
    total_elements: int
    page_count: int
    elapsed_seconds: float
    category_counts: dict[str, int]

    # Metric 1: element distribution ratio
    distribution_ratio: dict[str, float] = field(default_factory=dict)

    # Metric 2: table extraction success rate
    table_total: int = 0
    table_valid: int = 0

    # Metric 3: figure base64 extraction rate
    figure_total: int = 0
    figure_with_base64: int = 0

    @property
    def table_success_rate(self) -> float:
        if self.table_total == 0:
            return 0.0
        return self.table_valid / self.table_total

    @property
    def figure_base64_rate(self) -> float:
        if self.figure_total == 0:
            return 0.0
        return self.figure_with_base64 / self.figure_total


@dataclass
class BenchmarkReport:
    upstage: QualityReport
    local: QualityReport

    @property
    def speed_up_factor(self) -> float:
        if self.upstage.elapsed_seconds == 0:
            return 0.0
        return self.upstage.elapsed_seconds / self.local.elapsed_seconds


def analyze(result: ParseResult) -> QualityReport:
    category_counts = dict(Counter(el.category for el in result.elements))
    total = result.total_element_count

    distribution_ratio = {
        cat: round(count / total * 100, 1) if total else 0.0
        for cat, count in sorted(category_counts.items())
    }

    table_elements = [el for el in result.elements if el.category in _TABLE_CATEGORIES]
    figure_elements = [
        el for el in result.elements if el.category in _FIGURE_CATEGORIES
    ]

    table_valid = sum(
        1 for el in table_elements if _has_valid_table_structure(el.content)
    )
    figure_with_base64 = sum(1 for el in figure_elements if _element_has_base64(el))

    return QualityReport(
        source_filename=result.source_filename,
        total_elements=total,
        page_count=result.page_count,
        elapsed_seconds=result.elapsed_seconds,
        category_counts=category_counts,
        distribution_ratio=distribution_ratio,
        table_total=len(table_elements),
        table_valid=table_valid,
        figure_total=len(figure_elements),
        figure_with_base64=figure_with_base64,
    )


def compare(upstage_res: ParseResult, local_res: ParseResult) -> BenchmarkReport:
    return BenchmarkReport(upstage=analyze(upstage_res), local=analyze(local_res))


def _element_has_base64(element: ParsedElement) -> bool:
    base64_value = element.metadata.get("base64_encoding", "")
    return bool(base64_value)
