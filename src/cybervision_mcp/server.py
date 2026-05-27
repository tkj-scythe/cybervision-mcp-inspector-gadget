from __future__ import annotations

import argparse
import json
import os
from functools import lru_cache

from mcp.server.fastmcp import FastMCP

from cybervision_mcp.client import call_api
from cybervision_mcp.config import Settings, load_settings
from cybervision_mcp.openapi_index import (
    _DEFAULT_SPEC,
    find_endpoint,
    format_endpoint,
    get_endpoints,
    list_tags,
    search_endpoints as search_openapi_endpoints,
)

mcp = FastMCP(
    "Cisco Cyber Vision",
    instructions=(
        "MCP server for the Cisco Cyber Vision Classic REST API (v3). "
        "Use search_endpoints or get_endpoint_info to discover routes, then "
        "call_cybervision_api to execute requests. Typical inventory calls: "
        "GET /devices, GET /components, GET /networks/."
    ),
)


@lru_cache(maxsize=1)
def _settings() -> Settings:
    return load_settings()


@mcp.tool()
async def call_cybervision_api(
    method: str,
    path: str,
    query: dict | None = None,
    body: dict | list | None = None,
    path_params: dict | None = None,
) -> str:
    """Call any Cyber Vision Classic API endpoint.

    Args:
        method: HTTP method (GET, POST, PUT, PATCH, DELETE).
        path: API path relative to /api/3.0, e.g. "/components", "/devices", "/networks/".
        query: Optional query string parameters.
        body: Optional JSON body for POST/PUT/PATCH.
        path_params: Values for path placeholders, e.g. {"id": "..."} for "/devices/{id}".

    Examples:
        call_cybervision_api(method="GET", path="/devices", query={"page": 1, "size": 20})
        call_cybervision_api(method="GET", path="/components", query={"page": 1, "size": 50})
        call_cybervision_api(method="GET", path="/networks/")
    """
    return await call_api(
        _settings(),
        method=method,
        path=path,
        query=query,
        body=body,
        path_params=path_params,
    )


@mcp.tool()
def search_endpoints(query: str, tag: str | None = None, limit: int = 25) -> str:
    """Search the Cyber Vision OpenAPI spec by path, summary, operationId, or tag.

    Args:
        query: Search text (e.g. "components", "devices", "networks", "sensor").
        tag: Optional OpenAPI tag filter (e.g. "Components", "Devices", "CustomNetwork").
        limit: Maximum number of matches to return.
    """
    matches = search_openapi_endpoints(query, tag=tag, limit=limit)
    if not matches:
        return "No matching endpoints found."
    return "\n\n".join(format_endpoint(endpoint) for endpoint in matches)


@mcp.tool()
def get_endpoint_info(
    operation_id: str | None = None,
    path: str | None = None,
    method: str | None = None,
) -> str:
    """Get parameter and summary details for one API route.

    Provide either operation_id (e.g. getComponentList) or both path and method.
    """
    endpoint = find_endpoint(
        operation_id=operation_id,
        path=path,
        method=method,
    )
    if endpoint is None:
        return "Endpoint not found. Use search_endpoints to locate the route."
    return format_endpoint(endpoint)


@mcp.tool()
def list_all_endpoints(tag: str | None = None, limit: int = 50) -> str:
    """List API endpoints from the bundled OpenAPI spec.

    Args:
        tag: Optional filter by OpenAPI tag.
        limit: Maximum endpoints to return (default 50; spec has ~180 operations).
    """
    endpoints = get_endpoints()
    if tag:
        endpoints = [endpoint for endpoint in endpoints if tag in endpoint.tags]
    endpoints = endpoints[:limit]
    lines = [f"{endpoint.method} {endpoint.path} — {endpoint.summary}" for endpoint in endpoints]
    if tag is None:
        lines.append("")
        lines.append(f"Tags: {', '.join(list_tags())}")
    return "\n".join(lines)


@mcp.tool()
def get_api_spec_info() -> str:
    """Return metadata about the bundled OpenAPI specification."""
    endpoints = get_endpoints()
    with _DEFAULT_SPEC.open(encoding="utf-8") as handle:
        spec = json.load(handle)
    info = spec.get("info", {})
    return json.dumps(
        {
            "title": info.get("title"),
            "version": info.get("version"),
            "basePath": spec.get("basePath"),
            "endpoint_count": len(endpoints),
            "tags": list_tags(),
            "read_only_mode": _settings().read_only,
        },
        indent=2,
    )


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Cisco Cyber Vision MCP server (stdio transport)",
    )
    parser.add_argument(
        "-ro",
        "--read-only",
        action="store_true",
        help="Allow GET, HEAD, and OPTIONS only (block POST/PUT/PATCH/DELETE)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    if args.read_only:
        os.environ["CYBERVISION_READ_ONLY"] = "true"
    _settings.cache_clear()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
