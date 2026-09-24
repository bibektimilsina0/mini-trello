from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, workspaces, board, lists, cards, comments

app = FastAPI(title="TaskFlow API")

# Credentialed requests (cookies) reject a wildcard origin, so this must be
# an explicit origin, exactly like the Express version.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(workspaces.router)
app.include_router(board.router)
app.include_router(lists.router)
app.include_router(cards.router)
app.include_router(comments.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
