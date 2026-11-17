from __future__ import annotations

from fastapi import Header, HTTPException, Query, WebSocket, status

from app.config import settings


def verify_token(authorization: str | None = Header(default=None)) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    if token != settings.session_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")


def verify_ws_token(websocket: WebSocket) -> bool:
    token = websocket.query_params.get("token")
    if not token:
        auth = websocket.headers.get("authorization")
        if auth and auth.startswith("Bearer "):
            token = auth.removeprefix("Bearer ").strip()
    return token == settings.session_token
