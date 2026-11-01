# UniverseAI

Open-source AI workspace for local computers and cloud deployment. UniverseAI combines a Next.js interface, FastAPI services, Ollama local inference, PostgreSQL persistence, a knowledge base, and a constrained coding workspace.

## Current capabilities

- Streaming chat through Ollama or an OpenAI-compatible provider.
- Email/password registration and login with Argon2 password hashing and signed expiring tokens.
- Per-user conversation storage and deletion.
- PostgreSQL for cloud deployments; SQLite can be selected for local development.
- Knowledge base: TXT, Markdown, PDF and DOCX ingestion, per-account document storage, and keyword-based retrieval added to chat context.
- Model discovery and Ollama model downloads when using Ollama.
- AI coding agent with Ollama tool calling, per-account project workspaces, ZIP project import, file listing/reading/writing, and allowlisted test/build commands. Writes and checks require task-level approval; sensitive files and paths outside the workspace are blocked.
- Docker Compose deployment and GitHub Actions checks.

## Deploy to Render (free-tier test deployment)

The repository includes a Render Blueprint at `render.yaml`. It creates two free web services in Singapore:

- `universeai-api`: FastAPI backend.
- `universeai-web`: Next.js frontend.

The deployment uses OpenRouter for hosted inference. No Ollama model is downloaded to the Render service, and your phone does not run the AI model.

### Before deploying

1. Create a free account at [Neon](https://neon.tech/) and create a PostgreSQL project. Choose a region close to Singapore if available.
2. In the Neon dashboard, open **Connect**, select your database and role, and copy the pooled connection string. Use the URL in the `DATABASE_URL` field when Render asks for it. The URL should use TLS; if needed, change its prefix from `postgresql://` to `postgresql+psycopg://`.
3. Create an [OpenRouter](https://openrouter.ai/) account and an API key. Keep the key private.
4. Sign in to [Render](https://render.com/), choose **New → Blueprint**, and connect `veyl-dev/UniverseAI` on the `main` branch.
5. Review the two services. When prompted, provide:
   - `DATABASE_URL`: your Neon pooled PostgreSQL connection string, using the `postgresql+psycopg://` prefix.
   - `OPENAI_COMPAT_API_KEY`: your OpenRouter API key.
6. Apply the Blueprint. Wait for both services to finish deploying.
7. Open the `universeai-web` service in Render and visit its `onrender.com` URL. Register your account and start chatting.

Render generates `JWT_SECRET` automatically. Do not add API keys or database passwords to this repository. The Blueprint configures automatic deploys after GitHub Actions checks pass.

### Free-tier limitations

- Free Render web services sleep after 15 minutes without inbound traffic and can take about a minute to wake up.
- Free web-service filesystems are temporary. The Neon database preserves accounts, conversations, and knowledge-base records, but files in the coding workspace can disappear after restarts, sleep, or redeploys. Do not use the free deployment as permanent project-file storage.
- The hosted coding agent currently requires Ollama tool calling. This Render configuration uses OpenRouter, so normal chat works but the coding-agent task runner is not enabled for this deployment yet.
- The `openrouter/free` model router selects from available free models; availability, speed, context size, and quotas can change. Some free models may be unavailable at busy times.
- This is a testing/hobby deployment, not production hosting. Before public launch, add rate limiting, email verification, password reset, admin roles, audit logs, database migrations, abuse controls, and persistent object storage.

Render's free services are not a replacement for a paid always-on server. See [Render free services](https://render.com/docs/free).

## Local Docker quick start

1. Install Docker Engine and Compose.
2. Copy `.env.example` to `.env` and replace secrets with long random values.
3. Run `docker compose up --build -d`.
4. Pull a model: `docker compose exec ollama ollama pull qwen2.5:3b`.
5. Open http://localhost:3000 and register an account.

For a lightweight local SQLite setup, run `docker compose -f docker-compose.local.yml up --build -d` instead.

## Model providers

Ollama is the default local provider. To use an OpenAI-compatible endpoint, set:

- `AI_PROVIDER=openai-compatible`
- `OPENAI_COMPAT_BASE_URL`
- `OPENAI_COMPAT_MODEL`
- `OPENAI_COMPAT_API_KEY` (if required)

Then restart the backend. This supports compatible local inference servers and hosted gateways such as OpenRouter.

## Local database mode

Use `docker-compose.local.yml` to select SQLite for a single-machine deployment. For cloud deployments, configure PostgreSQL through `DATABASE_URL`.

## Coding workspace

Place each project inside `./workspace/user-<account-id>/` on the host. The API can list/read/write files there and run only configured development-check commands. The workspace is isolated by account. Do not mount your home directory, Docker socket, SSH keys, or host root into this workspace. The agent is a development helper, not a sandbox boundary against malicious code; use a disposable container/VM for untrusted repositories.

## Security

- Keep secrets in the hosting provider's secret manager; never commit `.env`.
- Use HTTPS, backups, firewall rules, and regular image/dependency updates in production.
- Authentication is enabled on API endpoints, but rate limiting, email verification, password reset, admin roles, audit logs, and formal database migrations remain required before public multi-user launch.
- Never run arbitrary model-generated shell commands on the host. Keep coding workspaces disposable and least-privileged.

## Roadmap

Semantic vector search, persistent memory controls, per-action approval prompts, image input, admin dashboard, mobile polish, rate limiting, database migrations, and cloud deployment hardening.

## License

MIT
