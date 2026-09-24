# TaskFlow — Team Collaboration Tool
### Complete build guide (FastAPI + React)

---

## 1. What you're building

A Trello/Linear-style app:

- Users sign up, create **Workspaces**
- Each workspace has **Boards** → **Lists** (columns) → **Cards**
- Cards can be dragged between lists in real time (WebSockets — every connected user sees moves instantly)
- Cards support comments, attachments, assignees, due dates
- Background job sends a daily email digest of due/overdue cards
- Everything is containerized and deployed with a public demo link

This single project touches: auth, relational data modeling, REST design, WebSockets, background jobs, file storage, testing, and deployment — the checklist most Python backend job postings ask for.

---

## 2. Architecture

```
┌─────────────┐        REST + WS        ┌──────────────────┐
│   React     │ ◄─────────────────────► │   FastAPI app     │
│  (Vite)     │                         │  (uvicorn)         │
└─────────────┘                         └─────────┬─────────┘
                                                   │
                          ┌────────────────────────┼───────────────────┐
                          │                        │                   │
                    ┌─────▼─────┐          ┌───────▼──────┐    ┌───────▼──────┐
                    │ PostgreSQL │          │    Redis      │    │   Celery      │
                    │ (SQLAlchemy)│         │ (pub/sub +    │    │  worker       │
                    │             │         │  cache)       │    │  (digest job) │
                    └─────────────┘         └───────────────┘    └───────────────┘
```

- **FastAPI** serves REST endpoints and a WebSocket endpoint
- **Redis pub/sub** broadcasts card-move events to all connected clients on a board (this is how real-time works across multiple server instances)
- **Celery + Redis (as broker)** runs the scheduled digest email job
- **PostgreSQL** is the source of truth; SQLAlchemy is the ORM

---

## 3. Tech stack

**Backend**
- FastAPI, Uvicorn
- SQLAlchemy 2.0 (async) + Alembic (migrations)
- Pydantic v2 (schemas/validation)
- PostgreSQL
- Redis (cache + pub/sub + Celery broker)
- Celery (background jobs)
- python-jose or PyJWT (JWT auth)
- passlib[bcrypt] (password hashing)
- pytest + httpx + pytest-asyncio (testing)

**Frontend**
- React + Vite
- TanStack Query (server state / caching — the React Query equivalent you already know)
- Zustand or Context (client state)
- native WebSocket API or socket.io-client (if you use socket.io instead of raw WS)
- dnd-kit (drag and drop for cards)
- Tailwind CSS

**Infra**
- Docker + docker-compose (local dev: api, worker, postgres, redis)
- Deploy: Render or Railway (backend + worker + Postgres + Redis), Vercel (frontend)

---

## 4. Database schema

```
users
  id (uuid, pk)
  email (unique)
  hashed_password
  name
  created_at

workspaces
  id (uuid, pk)
  name
  owner_id (fk -> users.id)

workspace_members
  workspace_id (fk)
  user_id (fk)
  role (owner | member)

boards
  id (uuid, pk)
  workspace_id (fk)
  title

lists
  id (uuid, pk)
  board_id (fk)
  title
  position (int, for ordering)

cards
  id (uuid, pk)
  list_id (fk)
  title
  description
  position (int)
  due_date (nullable)
  assignee_id (fk -> users.id, nullable)
  created_at

comments
  id (uuid, pk)
  card_id (fk)
  user_id (fk)
  body
  created_at

attachments
  id (uuid, pk)
  card_id (fk)
  file_url
  filename
```

`position` as an integer/float on lists and cards is how you implement drag-and-drop ordering without reindexing everything on every move (use fractional positions: moving a card between position 1 and 2 gives it position 1.5).

---

## 5. Folder structure

**Backend**
```
backend/
  app/
    main.py                 # FastAPI app instance, router includes
    config.py                # Pydantic Settings (env vars)
    database.py               # SQLAlchemy engine/session
    dependencies.py           # get_current_user, get_db, etc.
    models/                    # SQLAlchemy ORM models
      user.py, board.py, card.py ...
    schemas/                   # Pydantic request/response models
      user.py, board.py, card.py ...
    routers/                   # API route modules
      auth.py, workspaces.py, boards.py, cards.py, ws.py
    services/                  # business logic, kept out of routers
      auth_service.py, card_service.py
    tasks.py                   # Celery tasks (digest email)
    celery_app.py
  alembic/                     # migrations
  tests/
    test_auth.py, test_boards.py, test_cards.py
  Dockerfile
  requirements.txt (or pyproject.toml if using Poetry/uv)

frontend/
  src/
    api/                       # fetch wrappers / TanStack Query hooks
    components/
    pages/
    ws/                         # websocket client logic
  Dockerfile (optional)

docker-compose.yml
```

---

## 6. Build order (7 phases)

### Phase 1 — Auth & project skeleton (2–4 days)
- Set up FastAPI project, Postgres via docker-compose, Alembic migrations
- `User` model + signup/login endpoints
- Password hashing with bcrypt, JWT access + refresh tokens
- `get_current_user` dependency for protected routes
- **Concept to nail**: dependency injection in FastAPI (`Depends()`) — this is your Express middleware equivalent, but request-scoped and type-checked

### Phase 2 — Core CRUD: workspaces, boards, lists, cards (3–5 days)
- Full REST CRUD with Pydantic request/response schemas
- SQLAlchemy relationships (one-to-many, many-to-many for workspace members)
- Authorization checks (only workspace members can access a board)
- **Concept to nail**: SQLAlchemy async sessions and relationship loading (`selectinload` to avoid N+1 queries) — this is the most common thing Python backend interviews probe

### Phase 3 — Real-time updates via WebSockets (3–4 days)
- WebSocket endpoint `/ws/boards/{board_id}`
- On card move: broadcast the change via Redis pub/sub so every server instance/connected client updates
- Frontend: WebSocket client updates TanStack Query cache directly on incoming messages
- **Concept to nail**: why pub/sub is needed once you have more than one backend instance (in-memory broadcast alone won't scale)

### Phase 4 — Background jobs (2–3 days)
- Set up Celery worker + Redis broker
- Scheduled task (Celery beat) that emails users their due/overdue cards daily
- **Concept to nail**: difference between FastAPI `BackgroundTasks` (fire-and-forget, same process) vs Celery (separate worker process, retries, scheduling) — be ready to explain this trade-off in an interview

### Phase 5 — File uploads (1–2 days)
- Attachment upload endpoint (store to S3-compatible storage, e.g. Cloudflare R2 or local disk for demo)
- Signed URLs for secure download

### Phase 6 — Testing (2–3 days)
- pytest fixtures for a test database and authenticated test client
- Unit tests for services, integration tests for endpoints
- Aim for meaningful coverage on auth and card-move logic, not 100% everywhere

### Phase 7 — Docker, CI, deploy (2–3 days)
- `docker-compose.yml` wiring api + worker + postgres + redis
- GitHub Actions: run pytest on push
- Deploy API + worker + Postgres + Redis to Render/Railway
- Deploy React frontend to Vercel, point it at the deployed API
- Write a README with architecture diagram, setup instructions, and a live demo link — this README is what a recruiter actually reads

**Total realistic timeline**: 3–4 weeks at a steady evening/weekend pace.

---

## 7. Key snippets to anchor each concept

**FastAPI dependency for current user**
```python
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_jwt(token)
    user = await db.get(User, payload["sub"])
    if not user:
        raise HTTPException(status_code=401)
    return user
```

**SQLAlchemy async relationship**
```python
class Board(Base):
    __tablename__ = "boards"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    title: Mapped[str]
    lists: Mapped[list["List"]] = relationship(back_populates="board", lazy="selectin")
```

**WebSocket broadcast via Redis pub/sub**
```python
@router.websocket("/ws/boards/{board_id}")
async def board_ws(websocket: WebSocket, board_id: str):
    await websocket.accept()
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"board:{board_id}")
    async for message in pubsub.listen():
        if message["type"] == "message":
            await websocket.send_text(message["data"])
```

**Celery scheduled task**
```python
@celery_app.task
def send_daily_digest():
    users = get_users_with_due_cards()
    for user in users:
        send_email(user.email, build_digest(user))
```

---