"""
BizMind AI — Auth API
POST /auth/register, /auth/login, /auth/logout
Uses Supabase Auth with email/password.
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Annotated

from backend.core.supabase import get_supabase, get_supabase_admin
from backend.core.logging import get_logger
from backend.models.schemas import RegisterRequest, LoginRequest, AuthResponse

router = APIRouter()
logger = get_logger("auth")


def _get_token(authorization: Annotated[str | None, Header()] = None) -> str:
    """Extract Bearer token from Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    return authorization.split(" ", 1)[1]


@router.post("/register", response_model=AuthResponse)
async def register(payload: RegisterRequest):
    """Register a new user with email + password."""
    sb = get_supabase()
    try:
        resp = sb.auth.sign_up(
            {
                "email": payload.email,
                "password": payload.password,
                "options": {"data": {"full_name": payload.full_name}},
            }
        )
    except Exception as exc:
        logger.error("Registration failed", error=str(exc), email=payload.email)
        raise HTTPException(status_code=400, detail=str(exc))

    if not resp.user:
        raise HTTPException(status_code=400, detail="Registration failed. Check your email for confirmation.")

    logger.info("User registered", user_id=resp.user.id, email=payload.email)
    return AuthResponse(
        access_token=resp.session.access_token if resp.session else "",
        user_id=str(resp.user.id),
        email=resp.user.email or payload.email,
    )


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest):
    """Login with email + password, returns JWT access token."""
    sb = get_supabase()
    try:
        resp = sb.auth.sign_in_with_password(
            {"email": payload.email, "password": payload.password}
        )
    except Exception as exc:
        logger.warning("Login failed", error=str(exc), email=payload.email)
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if not resp.user or not resp.session:
        raise HTTPException(status_code=401, detail="Login failed.")

    logger.info("User logged in", user_id=resp.user.id)
    return AuthResponse(
        access_token=resp.session.access_token,
        user_id=str(resp.user.id),
        email=resp.user.email or payload.email,
    )


@router.post("/logout")
async def logout(token: str = Depends(_get_token)):
    """Invalidate the current session."""
    sb = get_supabase()
    try:
        sb.auth.sign_out()
    except Exception as exc:
        logger.warning("Logout error (ignoring)", error=str(exc))
    logger.info("User logged out")
    return {"message": "Logged out successfully."}


async def get_current_user(authorization: Annotated[str | None, Header()] = None) -> dict:
    """
    Dependency: validate JWT and return user dict.
    Usage: user = Depends(get_current_user)
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split(" ", 1)[1]
    sb = get_supabase()
    try:
        resp = sb.auth.get_user(token)
        if not resp.user:
            raise HTTPException(status_code=401, detail="Invalid or expired token.")
        
        # RBAC implementation: extract role from metadata, default to "user"
        metadata = resp.user.app_metadata or {}
        role = metadata.get("role", "user")
        is_admin = role == "admin"
        
        # For MVP/evaluation purposes, we can also check a specific email or user_metadata
        if not is_admin and resp.user.user_metadata:
             is_admin = resp.user.user_metadata.get("is_admin", False)
             if is_admin:
                 role = "admin"

        return {
            "id": str(resp.user.id), 
            "email": resp.user.email,
            "role": role,
            "is_admin": is_admin
        }
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """
    Dependency: ensures the current user has the admin role.
    Usage: admin_user = Depends(require_admin)
    """
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user
