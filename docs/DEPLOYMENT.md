# Deployment Guide

## Local development

Backend:

```bash
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The development frontend calls the API at `http://localhost:8000` unless `VITE_API_BASE_URL` is supplied.

## Docker Compose

```bash
docker compose up --build
```

Services:

- React/Nginx frontend: `http://localhost:8080`
- FastAPI backend: `http://localhost:8000`
- OpenAPI docs: `http://localhost:8000/docs`
- PostgreSQL: internal Compose network, persistent `pgdata` volume

The frontend Nginx configuration proxies `/api/` requests to the backend container. The compiled frontend uses `/api` as its production API base.

## Environment variables

Start from `.env.example`. Required live-provider values include:

- `DEMO_MODE=false`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`
- `ANTHROPIC_API_KEY`
- `ANTHROPIC_MODEL`

Never commit `.env`, OAuth tokens, or secret JSON files.

## Production hardening

Before production use:

1. Add identity, authentication, authorization, and tenant boundaries.
2. Store secrets in a managed secret service.
3. Use managed PostgreSQL with migrations and automated backups.
4. Put the frontend and API behind HTTPS and a reverse proxy/load balancer.
5. Restrict CORS to the production frontend origin.
6. Add request rate limiting and abuse protection.
7. Add centralized logs, traces, metrics, and alerts.
8. Configure provider OAuth consent and token rotation.
9. Define data retention and deletion policies for email content.
10. Run dependency, container, and application security scanning.

## CI

GitHub Actions verifies the backend test suite and React production build on pushes and pull requests to `main`.
