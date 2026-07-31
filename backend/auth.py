import os
import requests
import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session

from database import get_db
import models

# Set these on Railway once you've created your Clerk application:
# CLERK_JWKS_URL   — e.g. https://your-app.clerk.accounts.dev/.well-known/jwks.json
# CLERK_ISSUER     — e.g. https://your-app.clerk.accounts.dev
# CLERK_SECRET_KEY — starts with sk_, used only server-side to look up user details
CLERK_JWKS_URL = os.getenv("CLERK_JWKS_URL")
CLERK_ISSUER = os.getenv("CLERK_ISSUER")
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY")

_jwk_client = None


def _get_jwk_client():
    global _jwk_client
    if _jwk_client is None:
        if not CLERK_JWKS_URL:
            raise RuntimeError("CLERK_JWKS_URL is not set")
        _jwk_client = PyJWKClient(CLERK_JWKS_URL)
    return _jwk_client


def _verify_token(token: str) -> dict:
    jwk_client = _get_jwk_client()
    signing_key = jwk_client.get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        issuer=CLERK_ISSUER,
        options={"verify_aud": False},
    )


def _fetch_clerk_user(clerk_user_id: str) -> dict:
    """Look up a person's name/email from Clerk the first time we see them."""
    resp = requests.get(
        f"https://api.clerk.com/v1/users/{clerk_user_id}",
        headers={"Authorization": f"Bearer {CLERK_SECRET_KEY}"},
        timeout=5,
    )
    resp.raise_for_status()
    data = resp.json()
    name = " ".join(filter(None, [data.get("first_name"), data.get("last_name")])) or "Unnamed user"
    email = None
    for addr in data.get("email_addresses", []):
        if addr.get("id") == data.get("primary_email_address_id"):
            email = addr.get("email_address")
    return {"name": name, "email": email}


def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
) -> models.User:
    """FastAPI dependency: verifies the session token and returns (or creates) the local User."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    token = authorization.removeprefix("Bearer ").strip()

    try:
        payload = _verify_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    clerk_user_id = payload.get("sub")
    if not clerk_user_id:
        raise HTTPException(status_code=401, detail="Token missing subject")

    user = db.query(models.User).filter(models.User.clerk_user_id == clerk_user_id).first()
    if user is None:
        # First time we've seen this person — provision a local record, default role.
        info = _fetch_clerk_user(clerk_user_id)
        user = models.User(
            clerk_user_id=clerk_user_id,
            name=info["name"],
            email=info["email"],
            role="field_user",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def require_reviewer(user: models.User = Depends(get_current_user)) -> models.User:
    """FastAPI dependency: same as get_current_user, but rejects non-reviewers."""
    if user.role != "reviewer":
        raise HTTPException(status_code=403, detail="Reviewer access required")
    return user
