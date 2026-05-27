# Cisco Cyber Vision MCP Server

Python [MCP](https://modelcontextprotocol.io/) server for the **Cisco Cyber Vision Classic API v3** (bundled spec: 5.4.2). Exposes a generic API caller plus OpenAPI discovery tools, similar to a Meraki-style proxy.

## Requirements

- Python 3.11+
- Network access to your Cyber Vision Center
- API token from **Admin → API → Token**

## Setup

```bash
cd cybervision-mcp-inspector-gadget
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

cp .env.example .env
# Edit .env with your Center URL and token
```

### Environment variables

Credentials can live in the project `.env` file (recommended) or in the Cursor `env` block. When both are set, **`.env` wins`** so you can keep secrets out of `mcp.json`.

| Variable | Description |
|----------|-------------|
| `CYBERVISION_BASE_URL` | Center API root, e.g. `https://<center-host>/api/3.0` (no trailing slash) |
| `CYBERVISION_API_TOKEN` | Token value for header `x-token-id` |
| `CYBERVISION_VERIFY_SSL` | `true` / `false` (default `false` for self-signed certs) |
| `CYBERVISION_REQUEST_TIMEOUT` | Seconds (default `60`) |
| `CYBERVISION_MAX_RESPONSE_CHARS` | Truncate large JSON bodies (default `100000`) |

## Cursor configuration

Add to your MCP settings (merge `env` with your values):

```json
{
  "mcpServers": {
    "cybervision_inspector_gadget": {
      "command": "/absolute/path/to/cybervision-mcp-inspector-gadget/.venv/bin/python",
      "args": ["-m", "cybervision_mcp.server"],
      "cwd": "/absolute/path/to/cybervision-mcp-inspector-gadget",
      "env": {
        "CYBERVISION_VERIFY_SSL": "false"
      }
    }
  }
}
```

Or run the installed entry point:

```json
"command": "/absolute/path/to/.venv/bin/cybervision-mcp"
```

Restart Cursor after changing MCP config.

## Tools

| Tool | Purpose |
|------|---------|
| `call_cybervision_api` | Execute any REST call (GET/POST/PUT/PATCH/DELETE) |
| `search_endpoints` | Find routes in the OpenAPI spec |
| `get_endpoint_info` | Parameters and docs for one route |
| `list_all_endpoints` | Browse routes (optional tag filter) |
| `get_api_spec_info` | Spec version and tag list |

## Common calls (inventory)

```text
GET /devices?page=1&size=20
GET /components?page=1&size=50
GET /networks/
```

Examples via MCP:

```python
call_cybervision_api(method="GET", path="/devices", query={"page": 1, "size": 20})
call_cybervision_api(method="GET", path="/components", query={"page": 1, "size": 50})
call_cybervision_api(method="GET", path="/networks/")
```

Discover routes first:

```python
search_endpoints(query="components")
get_endpoint_info(operation_id="getComponentList")
```

## OpenAPI spec

`cisco-cyber-vision-api-v3.json` is loaded from the project root. When you upgrade to 5.5, replace that file and restart the MCP server.

## Security notes

- Do not commit `.env` or API tokens.
- Mutating API calls (POST/PUT/PATCH/DELETE) change Center data; Admin role is required for writes.
- `CYBERVISION_VERIFY_SSL=false` disables TLS certificate verification (acceptable for lab/self-signed centers only).

## Manual test

```bash
source .venv/bin/activate
export $(grep -v '^#' .env | xargs)
python -c "from cybervision_mcp.openapi_index import get_endpoints; print(len(get_endpoints()))"
```
