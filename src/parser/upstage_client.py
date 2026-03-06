from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import requests

from src.config.settings import ParseOptions


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_UPSTAGE_API_URL = "https://api.upstage.ai/v1/document-digitization"
_REQUEST_TIMEOUT_SECONDS = 300


# ---------------------------------------------------------------------------
# UpstageApiClient
# ---------------------------------------------------------------------------


class UpstageApiClient:
    """Thin wrapper around the Upstage Document Parse REST API.

    Uses the requests library directly instead of langchain_upstage
    for compatibility with Python 3.14+.
    """

    def __init__(self, api_key: str, options: ParseOptions) -> None:
        self._api_key = api_key
        self._options = options

    def parse_document(self, file_path: Path) -> tuple[list[dict[str, Any]], float]:
        """Call the Upstage Document Parse API for the given file.

        Args:
            file_path: Absolute path to the document to parse.

        Returns:
            A tuple of (elements, elapsed_seconds).
            Each element dict contains 'content' and metadata fields.

        Raises:
            FileNotFoundError: If the file does not exist.
            RuntimeError:      If the API call fails.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        start = time.perf_counter()
        response = self._call_api(file_path)
        elapsed = time.perf_counter() - start

        raw_elements = self._extract_elements(response)
        return raw_elements, elapsed

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _call_api(self, file_path: Path) -> dict[str, Any]:
        """Send the document to the Upstage API and return the JSON response."""
        headers = {"Authorization": f"Bearer {self._api_key}"}
        data = self._build_request_payload()

        with open(file_path, "rb") as document_file:
            files = {"document": (file_path.name, document_file, "application/octet-stream")}
            response = requests.post(
                _UPSTAGE_API_URL,
                headers=headers,
                data=data,
                files=files,
                timeout=_REQUEST_TIMEOUT_SECONDS,
            )

        if not response.ok:
            raise RuntimeError(
                f"Upstage API error {response.status_code}: {response.text}"
            )

        return response.json()

    def _build_request_payload(self) -> dict[str, Any]:
        """Build the form-data payload from ParseOptions."""
        opts = self._options
        payload: dict[str, Any] = {
            "model": opts.model,
            "ocr": opts.ocr,
            "output_formats": f'["{opts.output_format}"]',
            "coordinates": str(opts.coordinates).lower(),
            "chart_recognition": str(opts.chart_recognition).lower(),
        }
        if opts.base64_encoding:
            payload["base64_encoding"] = f'["{opts.base64_encoding[0]}"]'
        return payload

    @staticmethod
    def _extract_elements(response: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract parsed elements from the API response."""
        elements: list[dict[str, Any]] = response.get("elements", [])
        return [
            {
                "content": element.get("content", {}).get("html", "")
                or element.get("content", {}).get("text", "")
                or element.get("content", {}).get("markdown", ""),
                **{k: v for k, v in element.items() if k != "content"},
            }
            for element in elements
        ]
