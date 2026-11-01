# UniverseAI

Open-source self-hosted AI workspace for local computers and VPS deployments. Next.js + TypeScript frontend, FastAPI backend, Ollama inference, Docker Compose deployment.

## Quick start
1. Install Docker Engine and Compose.
2. Copy `.env.example` to `.env`.
3. Run `docker compose up --build -d`.
4. Pull a model: `docker compose exec ollama ollama pull qwen2.5:3b`.
5. Open http://localhost:3000.

This is an MVP foundation. Authentication, persistent conversations, RAG, cloud sync and production hardening remain on the roadmap. Do not expose Ollama or backend ports publicly.
