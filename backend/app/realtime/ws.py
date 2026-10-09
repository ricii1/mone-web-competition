from uuid import UUID

import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.models.live_session import LiveSession
from app.models.material import Material
from app.models.user import User
from app.realtime.channels import class_channel, live_session_channel, material_channel
from app.realtime.pubsub import subscribe
from app.services import class_service

router = APIRouter(tags=["realtime"])


def _authenticate(db: Session, token: str | None) -> User | None:
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        user_id = UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
    return db.get(User, user_id)


async def _forward_channel(websocket: WebSocket, channel: str) -> None:
    try:
        async for message in subscribe(channel):
            await websocket.send_text(message)
    except WebSocketDisconnect:
        pass


@router.websocket("/ws/materials/{material_id}")
async def material_progress_ws(
    websocket: WebSocket, material_id: UUID, token: str | None = None
) -> None:
    db = SessionLocal()
    try:
        user = _authenticate(db, token)
        material = db.get(Material, material_id)
        if user is None or material is None:
            await websocket.close(code=4401)
            return

        cls = class_service.get_class_or_404(db, material.class_id)
        is_owner = cls.teacher_id == user.id
        is_enrolled = class_service.is_enrolled(db, user.id, cls.id)
        if not (is_owner or is_enrolled):
            await websocket.close(code=4403)
            return

        await websocket.accept()
        await _forward_channel(websocket, material_channel(material_id))
    finally:
        db.close()


@router.websocket("/ws/classes/{class_id}")
async def class_events_ws(websocket: WebSocket, class_id: UUID, token: str | None = None) -> None:
    db = SessionLocal()
    try:
        user = _authenticate(db, token)
        if user is None:
            await websocket.close(code=4401)
            return

        cls = class_service.get_class_or_404(db, class_id)
        is_owner = cls.teacher_id == user.id
        is_enrolled = class_service.is_enrolled(db, user.id, class_id)
        if not (is_owner or is_enrolled):
            await websocket.close(code=4403)
            return

        await websocket.accept()
        await _forward_channel(websocket, class_channel(class_id))
    finally:
        db.close()


@router.websocket("/ws/live/{session_id}")
async def live_session_ws(websocket: WebSocket, session_id: UUID, token: str | None = None) -> None:
    db = SessionLocal()
    try:
        user = _authenticate(db, token)
        session = db.get(LiveSession, session_id)
        if user is None or session is None:
            await websocket.close(code=4401)
            return

        is_host = session.host_id == user.id
        is_participant = class_service.is_enrolled(db, user.id, session.class_id)
        if not (is_host or is_participant):
            await websocket.close(code=4403)
            return

        await websocket.accept()
        await _forward_channel(websocket, live_session_channel(session_id))
    finally:
        db.close()
