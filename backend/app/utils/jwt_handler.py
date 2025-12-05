"""
SmartKYC - JWT Handler
Utilities for creating and verifying JWT tokens
"""

import os
from datetime import datetime, timedelta
from typing import Optional

import jwt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-me-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary of data to encode in the token (typically {"sub": merchant_id})
        expires_delta: Optional custom expiration time delta

    Returns:
        Encoded JWT token string

    Example:
        token = create_access_token({"sub": "merchant-123"})
        token = create_access_token({"sub": "merchant-123"}, timedelta(hours=2))
    """
    to_encode = data.copy()

    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    # Encode JWT
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string to verify

    Returns:
        Decoded token payload if valid, None if invalid

    Example:
        payload = verify_token(token)
        if payload:
            merchant_id = payload.get("sub")
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        # Token has expired
        return None
    except Exception:
        # Invalid token (catch all JWT errors)
        return None


def decode_token(token: str) -> dict:
    """
    Decode a JWT token without verification (for debugging).

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Note:
        This does NOT verify the token signature. Use verify_token() for production.
    """
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except Exception as e:
        raise ValueError(f"Invalid token: {e}")


def get_token_expiry(token: str) -> Optional[datetime]:
    """
    Get the expiration time of a token.

    Args:
        token: JWT token string

    Returns:
        Expiration datetime if valid, None if invalid
    """
    payload = verify_token(token)
    if payload and "exp" in payload:
        return datetime.fromtimestamp(payload["exp"])
    return None
