from __future__ import annotations

from pathlib import Path
from typing import Any

from src.config.settings import AppSettings
from src.models.parse_result import ParsedElement, ParseResult
from src.parser.upstage_client import UpstageApiClient

_IMAGE_CATEGORIES = {"figure", "chart"}


class DocumentParser:

    def __init__(self, settings: AppSettings) -> None:
        self._client = UpstageApiClient(
            api_key=settings.api_key,
            options=settings.parse_options,
        )

    def parse(self, file_path: Path) -> ParseResult:
        raw_elements, elapsed = self._client.parse_document(file_path)

        elements = [self._map_to_element(raw) for raw in raw_elements]
        raw_output = self._build_raw_output(raw_elements)

        return ParseResult(
            source_filename=file_path.name,
            elements=elements,
            elapsed_seconds=elapsed,
            raw_output=raw_output,
        )

    @staticmethod
    def _map_to_element(raw: dict[str, Any]) -> ParsedElement:
        return ParsedElement(
            category=raw.get("category", "unknown"),
            content=raw.get("content", ""),
            page=raw.get("page", 1),
            coordinates=raw.get("coordinates", {}),
            metadata={
                k: v
                for k, v in raw.items()
                if k not in {"category", "content", "page", "coordinates"}
            },
        )

    @staticmethod
    def _build_raw_output(raw_elements: list[dict[str, Any]]) -> str:
        return "\n".join(el.get("content", "") for el in raw_elements)
