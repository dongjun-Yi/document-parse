from __future__ import annotations

import json
from pathlib import Path

from src.models.parse_result import ParseResult


def save_as_json(result: ParseResult, output_dir: Path) -> Path:
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

    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return output_path


def save_as_html(result: ParseResult, output_dir: Path) -> Path:
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


def save_as_markdown(result: ParseResult, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(result.source_filename).stem
    output_path = output_dir / f"{stem}_result.md"

    lines = [f"# Parse Result: {result.source_filename}\n"]
    for el in result.elements:
        lines.append(f"## [{el.category}] Page {el.page}")
        lines.append(el.content)
        lines.append("\n---\n")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path
