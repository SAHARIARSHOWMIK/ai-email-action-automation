# Deployment Guide

This project can run three ways:

1. **Local, no Docker** - `uvicorn` + `streamlit run`, SQLite (see main README).
2. **Local, Docker Compose** - full stack with PostgreSQL (this doc, section 1).
3. **Cloud demo** - backend + dashboard deployed separately, demo mode only (this doc, section 2).

---

## 1. Local stack with Docker Compose

This brings up PostgreSQL, the FastAPI backend, and the Streamlit dashboard
together.

```bash
docker compose up --build
```

- Dashboard: http://localhost:8501
- API docs (Swagger): http://localhost:8000/docs
- Health check: http://localhost:8000/health

By default `DEMO_MODE=true`, so the stack works immediately with **no
credentials** - sample emails, mock AI analysis, and mock execution are used.

### Running against real Gmail / Calendar / Anthropic

Create a `.env` file in the project root (docker compose loads it
automatically):

```env
DEMO_MODE=false
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
ANTHROPIC_API_KEY=sk-ant-...
```

> **Gmail OAuth note:** the first Gmail sync triggers an interactive OAuth
> consent flow (a browser window opens for login). This only works when
> running the backend **locally** (not inside a headless container or a
> cloud host), and should only ever be pointed at a **test Gmail account**,
> never your personal mailbox. For this reason, `DEMO_MODE=false` is intended
> for local development/demo only - the hosted cloud demo (below) always runs
> in demo mode.

---

## 2. Cloud demo deployment

The cloud demo deploys the backend and dashboard as **separate services**,
both running in `DEMO_MODE=true` with sample data. No Gmail or Anthropic
credentials are used in the cloud deployment.

### 2.1 Database

Use any managed PostgreSQL provider (Render, Railway, Supabase, Neon, etc.).
Copy the connection string - it will look like:

```text
postgresql://user:password@host:5432/dbname
```

### 2.2 Backend (FastAPI)

Deploy the root `Dockerfile` to a container platform (Render, Railway, Fly.io,
etc.) with these environment variables:

| Variable | Value |
| --- | --- |
| `ENV` | `production` |
| `DEMO_MODE` | `true` |
| `DATABASE_URL` | your managed Postgres connection string |
| `CONFIDENCE_THRESHOLD` | `0.75` |

The container listens on port `8000` and exposes:
- `GET /health` - use this as the platform's health check
- `GET /docs` - interactive API documentation
- `POST /emails/sync` - seeds the 8 demo emails on first call

### 2.3 Dashboard (Streamlit)

Deploy `dashboard/Dockerfile` (build context = project root) to the same or a
different platform, with:

| Variable | Value |
| --- | --- |
| `API_BASE_URL` | the public URL of the backend deployed in 2.2 |

The container listens on port `8501`.

### 2.4 Seeding the demo

After both services are live, open the dashboard and click **Sync Emails**
on the Emails page (or call `POST /emails/sync` on the backend directly).
This loads the 8 sample emails covering every supported intent, so a visitor
can immediately analyze, plan, approve, and execute actions.

### 2.5 Add the links to the README

Once deployed, add both URLs to the **Cloud demo** section of the main
`README.md`:

```markdown
## Live demo
- Dashboard: https://your-dashboard-url
- API docs: https://your-backend-url/docs
```

---

## Summary of safety guarantees in any deployment

- The cloud demo never holds real Gmail/Calendar/Anthropic credentials.
- `DEMO_MODE=false` (real Gmail/Calendar/AI) is local-only, due to the
  interactive OAuth flow and to avoid exposing personal mailbox access.
- No action ever runs without explicit human approval, regardless of mode
  (enforced in `app/services/approval.py`).
