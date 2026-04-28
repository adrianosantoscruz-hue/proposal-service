"""
Dependencias FastAPI — autenticacao JWT do Supabase.

Suporte a dois algoritmos:
  - ES256 (ECC P-256): chave atual do Supabase (verificada via JWKS)
  - HS256 (Shared Secret): chave legada (verificada via JWT_SECRET)
"""
import threading
from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError, jwk, jwt

from app.config import Settings, get_settings

bearer_scheme = HTTPBearer(auto_error=True)

_jwks_cache: list = []
_jwks_lock = threading.Lock()


def _load_jwks(supabase_url: str) -> list:
    global _jwks_cache
    with _jwks_lock:
        if _jwks_cache:
            return _jwks_cache
        try:
            url = f"{supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
            resp = httpx.get(url, timeout=10)
            resp.raise_for_status()
            _jwks_cache = resp.json().get("keys", [])
        except Exception:
            _jwks_cache = []
        return _jwks_cache


class AuthenticatedUser:
    def __init__(self, user_id: str, email: str | None = None, role: str | None = None):
        self.user_id = user_id
        self.email = email
        self.role = role

    def __repr__(self) -> str:
        return f"AuthenticatedUser(user_id={self.user_id!r}, email={self.email!r})"


def _decode_with_jwks(token: str, supabase_url: str) -> dict | None:
    keys = _load_jwks(supabase_url)
    for key_data in keys:
        try:
            public_key = jwk.construct(key_data)
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["ES256"],
                options={"verify_aud": False},
            )
            return payload
        except Exception:
            continue
    return None


def _decode_with_secret(token: str, secret: str) -> dict | None:
    if not secret:
        return None
    try:
        return jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
    except Exception:
        return None


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthenticatedUser:
    token = credentials.credentials

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalido ou expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        jwt.get_unverified_claims(token)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado. Faca login novamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise credentials_exception

    payload = (
        _decode_with_jwks(token, settings.SUPABASE_URL)
        or _decode_with_secret(token, getattr(settings, "SUPABASE_JWT_SECRET", ""))
    )

    if not payload:
        raise credentials_exception

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise credentials_exception

    return AuthenticatedUser(
        user_id=user_id,
        email=payload.get("email"),
        role=payload.get("role"),
    )


CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
