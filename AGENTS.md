# AGENTS.md

<!-- BEGIN CODEX GATEWAY BOOTSTRAP -->
## Codex Gateway bootstrap

This repository can run Codex in two modes:

- Simple mode: work locally without calling GatewayForgeLab.
- Gateway mode: connect to GatewayForgeLab as project `mediaforgelab`.

Read `.env` before relevant work.

Read `HANDOFF.md` after `.env` when resuming project work; it contains the current app state, implementation decisions, validated ports, data-import status, and proposed next step.

If `CODEX_GATEWAY_ENABLED=false`, use simple mode and do not call the Gateway.

If `CODEX_GATEWAY_ENABLED=true`, try `GATEWAY_BASE_URL`. If the Gateway is unavailable, continue in simple mode without blocking local work.

When the Gateway is available:
1. Use `GATEWAY_BASE_URL`, the Gateway bearer token configured in this repository's `.env` (for example `URG_GATEWAY_TOKEN`, `GATEWAYFORGELAB_GATEWAY_TOKEN`, or the repo-specific Gateway token env var), `GATEWAY_PROJECT_ID`, and `GATEWAY_PROJECT_TOKEN`.
2. Keep `GATEWAY_PROJECT_ID` + `GATEWAY_PROJECT_TOKEN` as the project scope. For REST endpoints that require it, send the Gateway bearer as `Authorization: Bearer ...` and send the project token separately, for example via `X-Project-Token` or `project_pass`.
3. Use the least-privileged identity that completes the task; do not use another project's identity. Use an admin/Gateway bearer only when the endpoint requires it or the user has authorized it.
4. Never reveal or persist token values in tracked files or conversation.
5. Load project context with `GET /api/projects/{projectId}/context` or the equivalent Gateway/MCP operation.
6. Check communications with `GET /api/projects/{projectId}/communications/inbox` and `GET /api/projects/{projectId}/communications/pending`, or the equivalent Gateway/MCP inbox operations.
7. Read and answer relevant pending messages before continuing.
8. Work only inside this project's responsibility and permissions.

Do not store tokens in tracked files. Keep real credentials in `.env`.
<!-- END CODEX GATEWAY BOOTSTRAP -->
