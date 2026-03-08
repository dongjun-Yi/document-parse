from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

from src.models.parse_result import ParsedElement, ParseResult


class LocalParser:
    def parse(self, file_path: Path) -> ParseResult:
        start_time = time.perf_counter()

        doc = fitz.open(str(file_path))
        elements = []
        full_text = []

        for page_num, page in enumerate(doc, start=1):
            text = page.get_text("text")
            if text.strip():
                element = ParsedElement(
                    category="paragraph",
                    content=text,
                    page=page_num,
                    metadata={"source": "pymupdf"},
                )
                elements.append(element)
                full_text.append(text)

        elapsed = time.perf_counter() - start_time
        doc.close()

        return ParseResult(
            source_filename=file_path.name,
            elements=elements,
            elapsed_seconds=elapsed,
            raw_output="\n".join(full_text),
        )
