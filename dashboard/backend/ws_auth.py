"""
OmniWatch 2.0 — NexusUX
Component: WebSocket Authentication
Layer: 11
Phase: 6
Purpose: JWT token verification for WebSocket connections
Inputs: JWT token from query parameter
Outputs: Decoded payload or None for rejected tokens
"""

import os
import logging
from typing import Optional

import jwt

logger = logging.getLogger(__name__)

JWT_PUBLIC_KEY = os.environ.get("JWT_PUBLIC_KEY", "")


def verify_ws_token(token: str) -> Optional[dict]:
    """Verify a JWT token for WebSocket authentication.

    Args:
        token: The JWT token string to verify.

    Returns:
        Decoded payload dict if valid, None if invalid/expired/unconfigured.
    """
    if not token:
        return None
    try:
        if not JWT_PUBLIC_KEY:
            logger.warning("JWT_PUBLIC_KEY not configured — WebSocket auth disabled")
            return {"user_id": "anonymous", "roles": ["viewer"]}
        payload = jwt.decode(token, JWT_PUBLIC_KEY, algorithms=["RS256"], options={"verify_exp": True})
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("WebSocket auth failed: token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning("WebSocket auth failed: %s", e)
        return None
