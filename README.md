# Cisco Cyber Vision MCP Server

Python [MCP](https://modelcontextprotocol.io/) server for the **Cisco Cyber Vision Classic API v3** (bundled spec: 5.5.0). Exposes a generic API caller plus OpenAPI discovery tools, similar to a Meraki-style proxy.

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
| `CYBERVISION_READ_ONLY` | `true` / `false` (default `false`) — block mutating API calls |

### Read-only mode

By default the server allows all HTTP methods (read-write). To block writes:

**CLI flag** (recommended):

```json
"args": ["-m", "cybervision_mcp.server", "-ro"]
```

Or:

```bash
cybervision-mcp --read-only
```

**Environment variable:**

```env
CYBERVISION_READ_ONLY=true
```

In read-only mode, `call_cybervision_api` only allows `GET`, `HEAD`, and `OPTIONS`. `POST`, `PUT`, `PATCH`, and `DELETE` are rejected before any request is sent. Discovery tools are unaffected.

Check `get_api_spec_info` for `"read_only_mode": true` to confirm the running server mode.

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

`cisco-cyber-vision-api-v3.json` is loaded from the project root. After replacing the spec file, **restart the MCP server** so the cached endpoint index is refreshed.

## Security notes

- Do not commit `.env` or API tokens.
- Mutating API calls (POST/PUT/PATCH/DELETE) change Center data; Admin role is required for writes.
- `CYBERVISION_VERIFY_SSL=false` disables TLS certificate verification (acceptable for lab/self-signed centers only).

## Publish to GitHub

Secrets must stay in `.env` only (gitignored). Before pushing:

```bash
chmod +x scripts/check-no-secrets.sh
./scripts/check-no-secrets.sh
```

Create the remote repository and push:

```bash
gh auth login
gh repo create cybervision-mcp-inspector-gadget --public --source=. --remote=origin --push
```

Use `--private` instead of `--public` if you prefer a private repository.

## CI and branch protection

GitHub Actions workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on every push and pull request to `main`:

- Installs the package
- Runs [`scripts/check-no-secrets.sh`](scripts/check-no-secrets.sh)
- Smoke-tests the bundled OpenAPI index

To satisfy [OpenSSF Scorecard branch protection](https://github.com/ossf/scorecard/blob/main/docs/checks.md#branch-protection), enable a rule on `main` and require the **CI / test** check to pass before merging.

## Manual test

```bash
source .venv/bin/activate
export $(grep -v '^#' .env | xargs)
python -c "from cybervision_mcp.openapi_index import get_endpoints; print(len(get_endpoints()))"
```
