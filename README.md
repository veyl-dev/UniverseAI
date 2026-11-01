# UniverseAI

Open-source, self-hosted AI workspace for local computers and VPS deployments. UniverseAI combines a Next.js interface, FastAPI services, Ollama local inference, PostgreSQL persistence, and a constrained coding-agent workspace.

## Current capabilities

- Local Ollama model discovery, streaming chat, and model downloads from the Model Library.
- Optional OpenAI-compatible provider support for vLLM, LM Studio, and hosted gateways through environment configuration.
- Email/password registration and login with Argon2 password hashing and signed expiring tokens.
- Per-user conversation storage and deletion.
- PostgreSQL for cloud deployments; SQLite can be selected with a local DATABASE_URL.
- Provider selection is configuration-driven; both Ollama and OpenAI-compatible chat endpoints are supported.
- AI coding agent with Ollama tool calling, per-account project workspaces, ZIP project import, file listing/reading/writing, and allowlisted test/build commands. Writes and checks require the user to enable approval for that task; sensitive files and paths outside the workspace are blocked.
- Knowledge base: TXT, Markdown, PDF and DOCX ingestion, per-account document storage, and keyword-based retrieval added to chat context.
- Model Library: discover installed Ollama models and pull additional models with live download progress.
- Configurable OpenAI-compatible chat provider for vLLM, LM Studio and hosted gateways.
- Docker Compose deployment and CI checks.

## Quick start

1. Install Docker Engine and Compose.
2. Copy `.env.example` to `.env` and replace both secrets with long random values.
3. Run `docker compose up --build -d`.
4. Pull a model: `docker compose exec ollama ollama pull qwen2.5:3b`.
5. Open http://localhost:3000 and register an account.

For a lightweight local SQLite setup, run `docker compose -f docker-compose.local.yml up --build -d` instead. The default Compose setup uses PostgreSQL and is suitable for VPS/cloud deployments.

Example secrets:
- Linux/macOS: `openssl rand -hex 32`
- PowerShell: `[Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32))`

## Model providers

Ollama is the default provider. To use an OpenAI-compatible endpoint, set `AI_PROVIDER=openai-compatible`, `OPENAI_COMPAT_BASE_URL`, `OPENAI_COMPAT_MODEL`, and optionally `OPENAI_COMPAT_API_KEY` in `.env`, then restart the stack. This supports compatible local inference servers and hosted gateways.

## Local database mode

Use `docker-compose.local.yml` to select SQLite for a single-machine deployment. The default Compose setup uses PostgreSQL for cloud/VPS deployments.

## Coding workspace

Place each project inside `./workspace/user-<account-id>/` on the host. The API can list/read/write files there and run only the configured development-check commands. The workspace is isolated by account. Do not mount your home directory, Docker socket, SSH keys, or host root into this workspace. The agent is a development helper, not a sandbox boundary against malicious code; use a disposable container/VM for untrusted repositories.

## Security and deployment

- Keep Ollama, PostgreSQL, and the backend private; expose only the frontend through a TLS reverse proxy.
- Set unique secrets; never commit `.env`.
- Use HTTPS, backups, firewall rules, and regular image/dependency updates in production.
- Authentication is enabled on API endpoints, but rate limiting, email verification, password reset, admin roles, audit logs, and formal database migrations remain required before public multi-user launch.
- Never run arbitrary model-generated shell commands on the host. Keep coding workspaces disposable and least-privileged.

## Roadmap

Semantic vector search, persistent memory controls, per-action approval prompts, image input, admin dashboard, mobile polish, rate limiting, database migrations, and cloud deployment automation are still planned.

## License

MIT
