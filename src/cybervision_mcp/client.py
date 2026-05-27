from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlencode

import httpx

from cybervision_mcp.config import READ_ONLY_METHODS, Settings


def _substitute_path(path: str, path_params: dict[str, Any] | None) -> str:
    if not path_params:
        return path
    resolved = path
    for key, value in path_params.items():
        resolved = resolved.replace(f"{{{key}}}", str(value))
    if "{" in resolved:
        raise ValueError(
            f"path still contains placeholders after substitution: {resolved}"
        )
    return resolved


def _format_body_preview(body: Any, max_chars: int) -> str:
    if body is None:
        return ""
    if isinstance(body, (dict, list)):
        text = json.dumps(body, indent=2, ensure_ascii=False)
    else:
        text = str(body)
    if len(text) > max_chars:
        return text[:max_chars] + f"\n... [truncated, {len(text)} total chars]"
    return text


async def call_api(
    settings: Settings,
    *,
    method: str,
    path: str,
    query: dict[str, Any] | None = None,
    body: Any | None = None,
    path_params: dict[str, Any] | None = None,
    extra_headers: dict[str, str] | None = None,
) -> str:
    method_upper = method.strip().upper()
    if method_upper not in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}:
        raise ValueError(f"unsupported HTTP method: {method}")

    if settings.read_only and method_upper not in READ_ONLY_METHODS:
        raise ValueError(
            f"read-only mode: {method_upper} {path} is blocked "
            "(only GET, HEAD, and OPTIONS are allowed). "
            "Restart without -ro or set CYBERVISION_READ_ONLY=false to allow writes."
        )

    api_path = path if path.startswith("/") else f"/{path}"
    api_path = _substitute_path(api_path, path_params)
    url = f"{settings.base_url}{api_path}"

    headers = {
        "accept": "application/json",
        "x-token-id": settings.api_token,
    }
    if extra_headers:
        headers.update(extra_headers)

    request_kwargs: dict[str, Any] = {
        "method": method_upper,
        "url": url,
        "headers": headers,
        "timeout": settings.request_timeout,
    }
    if query:
        request_kwargs["params"] = query
    if body is not None and method_upper not in {"GET", "HEAD", "OPTIONS"}:
        request_kwargs["json"] = body

    async with httpx.AsyncClient(verify=settings.verify_ssl) as client:
        response = await client.request(**request_kwargs)

    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            payload: Any = response.json()
            body_text = json.dumps(payload, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            body_text = response.text
    else:
        body_text = response.text

    body_text = _format_body_preview(body_text, settings.max_response_chars)

    request_line = f"{method_upper} {url}"
    if query:
        request_line += f"?{urlencode(query, doseq=True)}"

    parts = [
        request_line,
        f"status: {response.status_code} {response.reason_phrase}",
    ]
    if body_text:
        parts.append(body_text)
    return "\n".join(parts)
