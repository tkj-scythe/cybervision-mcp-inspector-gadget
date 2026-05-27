from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    base_url: str
    api_token: str
    verify_ssl: bool
    request_timeout: float
    max_response_chars: int


def load_settings() -> Settings:
    # Project .env overrides MCP config env (e.g. placeholder tokens in mcp.json).
    load_dotenv(_PROJECT_ROOT / ".env", override=True)

    base_url = os.environ.get("CYBERVISION_BASE_URL", "").strip().rstrip("/")
    api_token = os.environ.get("CYBERVISION_API_TOKEN", "").strip()
    if not base_url:
        raise ValueError(
            "CYBERVISION_BASE_URL is required (e.g. https://<center-host>/api/3.0)"
        )
    if not api_token:
        raise ValueError(
            "CYBERVISION_API_TOKEN is required (create one in Admin > API > Token)"
        )

    timeout_raw = os.environ.get("CYBERVISION_REQUEST_TIMEOUT", "60").strip()
    max_chars_raw = os.environ.get("CYBERVISION_MAX_RESPONSE_CHARS", "100000").strip()

    return Settings(
        base_url=base_url,
        api_token=api_token,
        verify_ssl=_env_bool("CYBERVISION_VERIFY_SSL", False),
        request_timeout=float(timeout_raw),
        max_response_chars=int(max_chars_raw),
    )
