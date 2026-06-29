# Security Policy

## Supported versions

| Version | Supported |
| ------- | --------- |
| 0.1.x   | Yes       |

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Instead, use [GitHub private vulnerability reporting](https://github.com/tkj-scythe/cybervision-mcp-inspector-gadget/security/advisories/new) for this repository.

Include:

- A description of the issue and potential impact
- Steps to reproduce
- Affected versions or commits
- Any suggested fix, if you have one

We aim to acknowledge reports within a few business days.

## Secrets and credentials

This project integrates with Cisco Cyber Vision using API tokens.

- Never commit `.env`, API tokens, or Center credentials to the repository
- Do not paste tokens into issues, pull requests, or chat logs
- Rotate any token that may have been exposed
- Use read-only mode (`-ro` / `CYBERVISION_READ_ONLY=true`) when write access is not required

## Secure use

- Prefer `.env` for local secrets instead of storing tokens in MCP client configuration
- Use TLS verification (`CYBERVISION_VERIFY_SSL=true`) when your Center has a trusted certificate
- Treat mutating API calls (`POST`, `PUT`, `PATCH`, `DELETE`) as changes to production Center data
