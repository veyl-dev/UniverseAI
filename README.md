# UniverseAI

Open-source, self-hosted AI workspace for local computers and VPS deployments. UniverseAI combines a Next.js interface, FastAPI services, Ollama local inference, PostgreSQL persistence, and a constrained coding-agent workspace.

## Current capabilities

- Local Ollama model discovery and streaming chat.
- Email/password registration and login with Argon2 password hashing and signed expiring tokens.
- Per-user conversation storage and deletion.
- PostgreSQL for cloud deployments; SQLite can be selected with a local DATABASE_URL.
- Provider adapter boundary (Ollama implemented; additional OpenAI-compatible providers can be added without coupling the UI to one vendor).
- Coding workspace: per-account project file listing, reading and writing, and allowlisted development checks. File paths are confined to each account workspace; command execution does not use a shell.
- Knowledge base: TXT, Markdown, PDF and DOCX ingestion, per-account document storage, and keyword-based retrieval added to chat context.
- Docker Compose deployment and CI checks.

## Quick start

1. Install Docker Engine and Compose.
2. Copy `.env.example` to `.env` and replace both secrets with long random values.
3. Run `docker compose up --build -d`.
4. Pull a model: `docker compose exec ollama ollama pull qwen2.5:3b`.
5. Open http://localhost:3000 and register an account.

Example secrets:
- Linux/macOS: `openssl rand -hex 32`
- PowerShell: `[Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32))`

## Local database mode

Set `DATABASE_URL=sqlite:////app/data/universeai.db` in `.env` to use the persistent SQLite volume instead of PostgreSQL. PostgreSQL is the default Compose database.

## Coding workspace

Place each project inside `./workspace/user-<account-id>/` on the host. The API can list/read/write files there and run only the configured development-check commands. The workspace is isolated by account. Do not mount your home directory, Docker socket, SSH keys, or host root into this workspace. The agent is a development helper, not a sandbox boundary against malicious code; use a disposable container/VM for untrusted repositories.

## Security and deployment

- Keep Ollama, PostgreSQL, and the backend private; expose only the frontend through a TLS reverse proxy.
- Set unique secrets; never commit `.env`.
- Use HTTPS, backups, firewall rules, and regular image/dependency updates in production.
- Authentication is enabled on API endpoints, but rate limiting, email verification, password reset, admin roles, audit logs, and formal database migrations remain required before public multi-user launch.
- Never run arbitrary model-generated shell commands on the host. Keep coding workspaces disposable and least-privileged.

## Roadmap

Semantic vector search, persistent memory controls, multi-provider API-key management, image input, model-driven agent plans with per-action approvals, admin dashboard, mobile polish, rate limiting, migrations, and cloud deployment automation are still planned.

## License

MIT
