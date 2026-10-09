from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    auth,
    classes,
    leaderboard,
    levels,
    live_sessions,
    materials,
    progress,
    questions,
)
from app.core.config import settings
from app.realtime import ws

app = FastAPI(title="EduMap API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    # loopback on any port, so localhost and 127.0.0.1 both work in dev
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(classes.router)
app.include_router(materials.router)
app.include_router(levels.router)
app.include_router(questions.router)
app.include_router(progress.router)
app.include_router(leaderboard.router)
app.include_router(live_sessions.router)
app.include_router(ws.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
