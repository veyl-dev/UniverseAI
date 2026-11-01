# UniverseAI

Open-source, self-hosted AI workspace for local computers and VPS deployments. UniverseAI combines a Next.js interface, FastAPI services, Ollama local inference, PostgreSQL persistence, and a constrained coding-agent workspace.

## Current capabilities

- Local Ollama model discovery and streaming chat.
- Email/password registration and login with Argon2 password hashing and signed expiring tokens.
- Per-user conversation storage and deletion.
- PostgreSQL for cloud deployments; SQLite can be selected with a local DATABASE_URL.
- Provider adapter boundary (Ollama implemented; additional OpenAI-compatible providers can be added without coupling the UI to one vendor).
- Coding-agent foundation: confined project file listing, reading and writing, and allowlisted development checks. All file paths are confined to WORKSPACE_ROOT; command execution does not use a shell.
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

Set `DATABASE_URL=sqlite:///./data/universeai.db` in your backend environment and create a writable data directory. PostgreSQL is the default Compose database.

## Coding workspace

Place a project inside `./workspace`. The API can list/read/write files there and run only the configured development-check commands. Do not mount your home directory, Docker socket, SSH keys, or host root into this workspace. The agent is a development helper, not a sandbox boundary against malicious code; use a disposable container/VM for untrusted repositories.

## Security and deployment

- Keep Ollama, PostgreSQL, and the backend private; expose only the frontend through a TLS reverse proxy.
- Set unique secrets; never commit `.env`.
- Use HTTPS, backups, firewall rules, and regular image/dependency updates in production.
- Authentication is enabled on API endpoints, but rate limiting, email verification, password reset, admin roles, audit logs, and formal database migrations remain required before public multi-user launch.
- Never run arbitrary model-generated shell commands on the host. Keep coding workspaces disposable and least-privileged.

## Roadmap

Document ingestion/RAG, durable memory controls, multi-provider API-key management, image input, agent approvals and task plans, admin dashboard, mobile polish, and cloud deployment automation are the next milestones.

## License

MIT
