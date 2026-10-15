from fastapi import HTTPException
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.config import settings


class BodyLimitMiddleware:
    """Reject oversized bodies while receiving, before multipart spooling or JSON parsing."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        path = scope.get("path", "")
        if scope["type"] != "http" or scope.get("method") != "POST":
            await self.app(scope, receive, send)
            return
        if path.startswith("/api/v1/classes/") and path.endswith("/materials"):
            limit = settings.max_upload_mb * 1024 * 1024 + 64 * 1024
        elif path in ("/api/v1/auth/login", "/api/v1/auth/register"):
            limit = 16 * 1024
        else:
            await self.app(scope, receive, send)
            return
        detail = "Data yang dikirim terlalu besar"
        headers = dict(scope.get("headers", []))
        try:
            length = int(headers.get(b"content-length", b"0"))
        except ValueError:
            await JSONResponse({"detail": "Ukuran permintaan tidak valid"}, status_code=400)(
                scope, receive, send
            )
            return
        if length > limit:
            await JSONResponse({"detail": detail}, status_code=413)(scope, receive, send)
            return
        received = 0

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > limit:
                    raise HTTPException(status_code=413, detail=detail)
            return message

        await self.app(scope, limited_receive, send)
