from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
import os

load_dotenv()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_OUTPUT_DIR = "outputs"
_DEFAULT_MODEL = "document-parse"
_VALID_OCR_VALUES = ("auto", "force", "off")
_VALID_OUTPUT_FORMATS = ("html", "text", "markdown")


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ParseOptions:
    """Upstage Document Parse API options."""

    model: str = _DEFAULT_MODEL
    ocr: Literal["auto", "force", "off"] = "auto"
    output_format: Literal["html", "text", "markdown"] = "html"
    coordinates: bool = True
    chart_recognition: bool = True
    base64_encoding: list[str] = field(default_factory=lambda: ["figure"])


@dataclass
class AppSettings:
    """Application-wide settings loaded from environment variables."""

    api_key: str
    output_dir: Path
    parse_options: ParseOptions


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


def load_settings(parse_options: ParseOptions | None = None) -> AppSettings:
    """Load and validate application settings from environment variables.

    Raises:
        EnvironmentError: If UPSTAGE_API_KEY is not set.
    """
    api_key = os.getenv("UPSTAGE_API_KEY", "")
    if not api_key:
        raise EnvironmentError(
            "UPSTAGE_API_KEY is not set. "
            "Copy .env.example to .env and fill in your API key."
        )

    raw_output_dir = os.getenv("OUTPUT_DIR", _DEFAULT_OUTPUT_DIR)
    output_dir = Path(raw_output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    return AppSettings(
        api_key=api_key,
        output_dir=output_dir,
        parse_options=parse_options or ParseOptions(),
    )
