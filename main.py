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
    --benchmark Enable benchmark mode (compare with local open-source parser)
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
from src.parser.local_parser import LocalParser
from src.reporter.quality_analyzer import analyze, compare
from src.reporter.result_saver import save_as_html, save_as_json, save_as_markdown

console = Console(file=sys.stdout, highlight=False)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rag-doc-parser",
        description="Evaluate document parser performance using Upstage API",
    )
    parser.add_argument(
        "--file",
        default="demo_pdf_file.pdf",
        help="Path to the PDF/image file to parse (default: demo_pdf_file.pdf)",
    )
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
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Enable side-by-side benchmark with open-source parser",
    )
    return parser


def run_parse_pipeline(args: argparse.Namespace) -> int:
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

    console.print(
        Panel.fit(
            f"[bold]File:[/bold] {file_path.name}\n"
            f"[bold]OCR:[/bold] {args.ocr}  "
            f"[bold]Format:[/bold] {args.output_format}"
            + (
                f"\n[bold]Mode:[/bold] [yellow]Benchmark[/yellow]"
                if args.benchmark
                else ""
            ),
            title="[cyan]RAG Document Parser[/cyan]",
        )
    )

    # 1. Upstage API Parsing
    with console.status("[cyan]Upstage API로 파싱 중...[/cyan]"):
        parser = DocumentParser(settings)
        upstage_result = parser.parse(file_path)

    json_path = save_as_json(upstage_result, output_dir)
    html_path = save_as_html(upstage_result, output_dir)
    md_path = save_as_markdown(upstage_result, output_dir)

    if args.benchmark:
        # 2. Local Parsing
        with console.status(
            "[magenta]로컬 오픈소스 파서(PyMuPDF)로 파싱 중...[/magenta]"
        ):
            local_parser = LocalParser()
            local_result = local_parser.parse(file_path)

        benchmark_report = compare(upstage_result, local_result)
        _print_benchmark_report(benchmark_report)
    else:
        report = analyze(upstage_result)
        _print_summary(report)

    _print_file_info(json_path, html_path, md_path)
    return 0


def _print_benchmark_report(report) -> None:
    table = Table(
        title="[Benchmark] Upstage vs. Local (PyMuPDF)",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("성능 지표", style="bold")
    table.add_column("Upstage API", justify="right")
    table.add_column("Local Parser", justify="right")

    table.add_row(
        "소요 시간 (초)",
        f"{report.upstage.elapsed_seconds:.2f}s",
        f"{report.local.elapsed_seconds:.2f}s",
    )
    table.add_row(
        "총 추출 요소 수",
        str(report.upstage.total_elements),
        str(report.local.total_elements),
    )
    table.add_row(
        "표(Table) 보호 개수",
        str(report.upstage.table_total),
        str(report.local.table_total),
    )
    table.add_row(
        "이미지(Figure) 개수",
        str(report.upstage.figure_total),
        str(report.local.figure_total),
    )

    table.add_section()
    speed_factor = (
        report.local.elapsed_seconds / report.upstage.elapsed_seconds
        if report.upstage.elapsed_seconds > 0
        else 0
    )
    table.add_row(
        "[bold]상대 속도[/bold]",
        "1.0x (Standard)",
        f"{1/speed_factor:.1f}x Faster" if speed_factor > 0 else "N/A",
    )

    console.print(table)
    console.print(
        Panel(
            "[bold]Benchmark 분석:[/bold]\n"
            "1. [cyan]Upstage API[/cyan]는 표(Table)와 이미지(Figure)를 구조적으로 완벽하게 분리하여 추출하지만 네트워크 대기 시간이 발생합니다.\n"
            "2. [magenta]로컬 파서[/magenta]는 속도가 매우 빠르지만, 대부분의 요소를 단순 텍스트(paragraph)로만 인식하는 경향이 있습니다.",
            border_style="dim",
        )
    )


def _print_summary(report) -> None:
    _print_distribution_table(report)
    _print_table_success_rate(report)
    _print_figure_base64_rate(report)


def _print_distribution_table(report) -> None:
    table = Table(
        title="[1] 요소 분포 비율", show_header=True, header_style="bold cyan"
    )
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
    table = Table(
        title="[2] 표 추출 성공률", show_header=True, header_style="bold cyan"
    )
    table.add_column("항목", style="bold")
    table.add_column("값", justify="right")

    rate = (
        (report.table_valid / report.table_total * 100) if report.table_total else 0.0
    )
    table.add_row("전체 표 요소 수", str(report.table_total))
    table.add_row("유효한 <td> 구조 수", str(report.table_valid))
    table.add_row("성공률", f"{rate:.1f}%")
    console.print(table)


def _print_figure_base64_rate(report) -> None:
    table = Table(
        title="[3] 이미지 base64 추출률", show_header=True, header_style="bold cyan"
    )
    table.add_column("항목", style="bold")
    table.add_column("값", justify="right")

    rate = report.figure_base64_rate * 100
    table.add_row("전체 figure/chart 요소 수", str(report.figure_total))
    table.add_row("base64 데이터 존재 수", str(report.figure_with_base64))
    table.add_row("추출률", f"{rate:.1f}%")
    console.print(table)


def _print_file_info(json_path: Path, html_path: Path, md_path: Path) -> None:
    console.print(
        f"\n[green][OK][/green] 결과 저장 완료\n"
        f"  • JSON: [dim]{json_path}[/dim]\n"
        f"  • HTML: [dim]{html_path}[/dim]\n"
        f"  • MD:   [dim]{md_path}[/dim]"
    )


if __name__ == "__main__":
    arg_parser = build_argument_parser()
    args = arg_parser.parse_args()
    sys.exit(run_parse_pipeline(args))
