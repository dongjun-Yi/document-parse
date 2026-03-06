"""
CLI entry point for RAG Document Parser performance evaluation.

Usage:
    python main.py --file <path_to_pdf> [options]

Options:
    --file      Path to the document file to parse (required)
    --ocr       OCR mode: auto | force | off  (default: auto)
    --format    Output format: html | text | markdown  (default: html)
    --no-coords Disable coordinate extraction
    --output    Output directory  (default: outputs/)
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

# Force UTF-8 output to avoid UnicodeEncodeError on Windows cp949 consoles
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.config.settings import ParseOptions, load_settings
from src.parser.document_parser import DocumentParser
from src.reporter.quality_analyzer import analyze
from src.reporter.result_saver import save_as_html, save_as_json

console = Console(file=sys.stdout, highlight=False)


# ---------------------------------------------------------------------------
# CLI argument parsing
# ---------------------------------------------------------------------------


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rag-doc-parser",
        description="Evaluate document parser performance using Upstage API",
    )
    parser.add_argument("--file", required=True, help="Path to the PDF/image file to parse")
    parser.add_argument(
        "--ocr",
        choices=["auto", "force", "off"],
        default="auto",
        help="OCR mode (default: auto)",
    )
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=["html", "text", "markdown"],
        default="html",
        help="Output format (default: html)",
    )
    parser.add_argument(
        "--no-coords",
        action="store_true",
        help="Disable coordinate extraction",
    )
    parser.add_argument(
        "--output",
        default="outputs",
        help="Output directory (default: outputs/)",
    )
    return parser


# ---------------------------------------------------------------------------
# Core pipeline
# ---------------------------------------------------------------------------


def run_parse_pipeline(args: argparse.Namespace) -> int:
    """Execute the full parse → save → report pipeline.

    Returns:
        Exit code (0 = success, 1 = failure).
    """
    file_path = Path(args.file)
    if not file_path.exists():
        console.print(f"[red]Error:[/red] File not found: {file_path}")
        return 1

    parse_options = ParseOptions(
        ocr=args.ocr,
        output_format=args.output_format,
        coordinates=not args.no_coords,
    )

    try:
        settings = load_settings(parse_options)
    except EnvironmentError as exc:
        console.print(f"[red]Configuration error:[/red] {exc}")
        return 1

    output_dir = Path(args.output)

    console.print(Panel.fit(
        f"[bold]File:[/bold] {file_path.name}\n"
        f"[bold]OCR:[/bold] {args.ocr}  "
        f"[bold]Format:[/bold] {args.output_format}",
        title="[cyan]RAG Document Parser[/cyan]",
    ))

    with console.status("[cyan]Upstage API로 파싱 중...[/cyan]"):
        parser = DocumentParser(settings)
        result = parser.parse(file_path)

    json_path = save_as_json(result, output_dir)
    html_path = save_as_html(result, output_dir)
    report = analyze(result)

    _print_summary(report)
    _print_file_info(json_path, html_path)
    return 0


# ---------------------------------------------------------------------------
# Rich output helpers
# ---------------------------------------------------------------------------


def _print_summary(report) -> None:
    """Print three extraction quality metrics as rich tables."""
    _print_distribution_table(report)
    _print_table_success_rate(report)
    _print_figure_base64_rate(report)


def _print_distribution_table(report) -> None:
    """Metric 1: Print element distribution ratio by category."""
    table = Table(title="[1] 요소 분포 비율", show_header=True, header_style="bold cyan")
    table.add_column("카테고리", style="bold")
    table.add_column("개수", justify="right")
    table.add_column("비율 (%)", justify="right")

    for category, ratio in report.distribution_ratio.items():
        count = report.category_counts.get(category, 0)
        table.add_row(category, str(count), f"{ratio:.1f}%")

    table.add_section()
    table.add_row("[bold]합계[/bold]", str(report.total_elements), "100.0%")
    console.print(table)


def _print_table_success_rate(report) -> None:
    """Metric 2: Print table extraction success rate (<td> structure validity)."""
    table = Table(title="[2] 표 추출 성공률", show_header=True, header_style="bold cyan")
    table.add_column("항목", style="bold")
    table.add_column("값", justify="right")

    rate = (report.table_valid / report.table_total * 100) if report.table_total else 0.0
    table.add_row("전체 표 요소 수", str(report.table_total))
    table.add_row("유효한 <td> 구조 수", str(report.table_valid))
    table.add_row("성공률", f"{rate:.1f}%")
    console.print(table)


def _print_figure_base64_rate(report) -> None:
    """Metric 3: Print figure base64 extraction rate."""
    table = Table(title="[3] 이미지 base64 추출률", show_header=True, header_style="bold cyan")
    table.add_column("항목", style="bold")
    table.add_column("값", justify="right")

    rate = report.figure_base64_rate * 100
    table.add_row("전체 figure/chart 요소 수", str(report.figure_total))
    table.add_row("base64 데이터 존재 수", str(report.figure_with_base64))
    table.add_row("추출률", f"{rate:.1f}%")
    console.print(table)


def _print_file_info(json_path: Path, html_path: Path) -> None:
    console.print(
        f"\n[green][OK][/green] 결과 저장 완료\n"
        f"  • JSON: [dim]{json_path}[/dim]\n"
        f"  • HTML: [dim]{html_path}[/dim]"
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    arg_parser = build_argument_parser()
    args = arg_parser.parse_args()
    sys.exit(run_parse_pipeline(args))
