from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

_HTTP_METHODS = frozenset({"get", "post", "put", "patch", "delete", "head", "options"})

_DEFAULT_SPEC = (
    Path(__file__).resolve().parents[2] / "cisco-cyber-vision-api-v3.json"
)


@dataclass(frozen=True)
class Endpoint:
    path: str
    method: str
    operation_id: str | None
    summary: str
    description: str
    tags: tuple[str, ...]
    parameters: tuple[dict[str, Any], ...]


def _load_spec_dict(spec_path: Path | None = None) -> dict[str, Any]:
    path = spec_path or _DEFAULT_SPEC
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def get_endpoints(spec_path: str | None = None) -> tuple[Endpoint, ...]:
    path = Path(spec_path) if spec_path else _DEFAULT_SPEC
    spec = _load_spec_dict(path)
    endpoints: list[Endpoint] = []

    for api_path, path_item in spec.get("paths", {}).items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method not in _HTTP_METHODS or not isinstance(operation, dict):
                continue
            params = operation.get("parameters") or []
            endpoints.append(
                Endpoint(
                    path=api_path,
                    method=method.upper(),
                    operation_id=operation.get("operationId"),
                    summary=operation.get("summary") or "",
                    description=operation.get("description") or "",
                    tags=tuple(operation.get("tags") or []),
                    parameters=tuple(params if isinstance(params, list) else []),
                )
            )

    endpoints.sort(key=lambda item: (item.path, item.method))
    return tuple(endpoints)


def _tokenize(query: str) -> list[str]:
    return [part for part in re.split(r"\s+", query.strip().lower()) if part]


def _score_endpoint(endpoint: Endpoint, tokens: list[str]) -> int:
    if not tokens:
        return 0
    path_lower = endpoint.path.lower()
    summary_lower = endpoint.summary.lower()
    op_lower = (endpoint.operation_id or "").lower()
    tag_text = " ".join(tag.lower() for tag in endpoint.tags)
    description_lower = endpoint.description.lower()

    score = 0
    for token in tokens:
        if token in path_lower:
            score += 40
        if token in summary_lower or token in op_lower:
            score += 25
        if token in tag_text:
            score += 15
        if token in description_lower:
            score += 5
    return score


def search_endpoints(
    query: str,
    *,
    tag: str | None = None,
    limit: int = 25,
    spec_path: str | None = None,
) -> list[Endpoint]:
    tokens = _tokenize(query)
    results: list[tuple[int, Endpoint]] = []

    for endpoint in get_endpoints(spec_path):
        if tag and tag not in endpoint.tags:
            continue
        score = _score_endpoint(endpoint, tokens)
        if tokens and score == 0:
            continue
        results.append((score if tokens else 0, endpoint))

    results.sort(key=lambda item: (-item[0], item[1].path, item[1].method))
    return [endpoint for _, endpoint in results[:limit]]


def find_endpoint(
    *,
    path: str | None = None,
    method: str | None = None,
    operation_id: str | None = None,
    spec_path: str | None = None,
) -> Endpoint | None:
    method_upper = method.upper() if method else None
    normalized_path = path if not path or path.startswith("/") else f"/{path}"

    for endpoint in get_endpoints(spec_path):
        if operation_id and endpoint.operation_id == operation_id:
            return endpoint
        if (
            normalized_path
            and method_upper
            and endpoint.path == normalized_path
            and endpoint.method == method_upper
        ):
            return endpoint
    return None


def format_endpoint(endpoint: Endpoint) -> str:
    lines = [
        f"{endpoint.method} {endpoint.path}",
        f"operationId: {endpoint.operation_id or '(none)'}",
        f"summary: {endpoint.summary or '(none)'}",
    ]
    if endpoint.description:
        lines.append(f"description: {endpoint.description}")
    if endpoint.tags:
        lines.append(f"tags: {', '.join(endpoint.tags)}")
    if endpoint.parameters:
        lines.append("parameters:")
        for param in endpoint.parameters:
            location = param.get("in", "?")
            name = param.get("name", "?")
            required = "required" if param.get("required") else "optional"
            description = param.get("description", "")
            param_type = param.get("type") or (
                param.get("schema", {}).get("type")
                if isinstance(param.get("schema"), dict)
                else None
            )
            detail = f"  - {location} {name} ({required}"
            if param_type:
                detail += f", {param_type}"
            detail += ")"
            if description:
                detail += f": {description}"
            lines.append(detail)
    return "\n".join(lines)


def list_tags(spec_path: str | None = None) -> list[str]:
    tags: set[str] = set()
    for endpoint in get_endpoints(spec_path):
        tags.update(endpoint.tags)
    return sorted(tags)
