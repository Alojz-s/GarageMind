# GarageMind

Hub for underground metal bands: public landing, sign-in, band directory, and admin tools.

**Stack:** FastAPI, PostgreSQL, React (TypeScript, Vite). Session cookie auth; Vite proxies `/api` to the backend in development.

## Run locally (Git Bash, Windows)

```bash
cp .env.example .env
docker compose up -d

cd backend
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements-dev.txt
alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload
```

```bash
cd frontend
npm install
npm run dev
```

- App: http://localhost:5173  
- API docs: http://localhost:8000/api/docs  

## Checks

```bash
cd backend && pytest && ruff check . && ruff format --check .
cd frontend && npm run lint && npm run build
```

## Main routes

| Path | Description |
|------|-------------|
| `/` | Public landing |
| `/login` | Sign in |
| `/bands` | Band directory (signed in) |
| `/admin/users`, `/admin/settings` | Administration |

Initial admin: login `ADMIN` (password in `.env` — change on first sign-in). See `.env.example` for seed users.
