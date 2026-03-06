from __future__ import annotations

import json
from pathlib import Path

from src.models.parse_result import ParseResult


def save_as_json(result: ParseResult, output_dir: Path) -> Path:
    """Save ParseResult as a structured JSON file.

    Returns the path of the saved file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(result.source_filename).stem
    output_path = output_dir / f"{stem}_result.json"

    payload = {
        "source_filename": result.source_filename,
        "elapsed_seconds": result.elapsed_seconds,
        "total_elements": result.total_element_count,
        "page_count": result.page_count,
        "elements": [
            {
                "category": el.category,
                "page": el.page,
                "content": el.content,
                "coordinates": el.coordinates,
                "metadata": el.metadata,
            }
            for el in result.elements
        ],
    }

    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def save_as_html(result: ParseResult, output_dir: Path) -> Path:
    """Save the raw HTML output from the API to a standalone HTML file.

    Returns the path of the saved file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(result.source_filename).stem
    output_path = output_dir / f"{stem}_raw.html"

    html_content = (
        "<!DOCTYPE html>\n<html lang='ko'>\n<head>\n"
        "<meta charset='UTF-8'>\n"
        f"<title>{result.source_filename} — Parse Result</title>\n"
        "</head>\n<body>\n"
        f"{result.raw_output}\n"
        "</body>\n</html>"
    )
    output_path.write_text(html_content, encoding="utf-8")
    return output_path
