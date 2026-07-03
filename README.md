# AIMark — Brand Brain

AI marketing-content tool built around a **Brand Brain**: a setup phase that captures a
brand's strategy, audience, voice, and competitive intel once, then feeds an AI
generation engine on every content request.

Built **phase by phase**, mirroring the 6 setup stages from the spec:

| Phase | Stage | Status |
|-------|-------|--------|
| 1 | Brand inputs (vision, goal, moat) | ✅ Done |
| 2 | ICP builder (personas + variants) | ⏳ Next |
| 3 | Voice codifier (samples, banned words, rewrite pairs) | ⏳ |
| 4 | Competitor agent + Knowledge base | ⏳ |
| 5 | Pillar synthesis (4–6 approved pillars) | ⏳ |
| 6 | Brand context store (the brand brain) | ⏳ |

## Stack

- **Backend:** FastAPI · SQLAlchemy 2 (async) · Alembic · PostgreSQL 16 · managed with `uv`
- **Frontend:** React + TypeScript + Vite
- **DB:** Postgres (`aimark` db / `aimark` role)

## Layout

```
AIMark/
├── backend/
│   ├── app/
│   │   ├── api/        # routers (brands.py)
│   │   ├── core/       # config/settings
│   │   ├── db/         # engine, session, declarative base
│   │   ├── models/     # SQLAlchemy models (Brand)
│   │   ├── schemas/    # Pydantic schemas
│   │   └── main.py     # FastAPI app
│   └── alembic/        # migrations
└── frontend/
    └── src/
        ├── components/ # BrandInputs.tsx
        ├── api.ts      # typed API client
        ├── phases.ts   # 6-phase model
        └── App.tsx     # phase navigator shell
```

## Running locally

Prereqs: Postgres running with an `aimark` database/role (see below), `uv`, Node 18+.

```bash
# one-time DB setup (if not already done)
createdb aimark            # or via the CREATE ROLE/DATABASE statements

# backend  (http://localhost:8000, docs at /docs)
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000

# frontend (http://localhost:5173, proxies /api → :8000)
cd frontend
npm install
npm run dev
```

## Phase 1 API

| Method | Path | Purpose |
|--------|------|---------|
| GET    | `/api/brands`        | list brands |
| POST   | `/api/brands`        | create brand |
| GET    | `/api/brands/{id}`   | fetch one |
| PATCH  | `/api/brands/{id}`   | partial update |
| DELETE | `/api/brands/{id}`   | delete |

`Brand` = `{ name, vision, goal, moat }` (+ id, timestamps). `name` required; the
rest optional and trimmed. Each later phase adds related tables keyed on `brand.id`.

## Adding a phase

1. Backend: add model in `app/models/`, register in `app/models/__init__.py`,
   `alembic revision --autogenerate`, `alembic upgrade head`, add schemas + router.
2. Frontend: add a component, flip its entry in `src/phases.ts` from `upcoming` to
   `active`, wire it into `App.tsx`.
