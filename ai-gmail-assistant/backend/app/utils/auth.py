"""Authentication utilities for JWT tokens and password hashing."""

from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from passlib.context import CryptContext
from app.utils.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.secret_key, 
        algorithm=settings.algorithm
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(
            token, 
            settings.secret_key, 
            algorithms=[settings.algorithm]
        )
        return payload
    except Exception:
        return None


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def encrypt_token(token: str) -> str:
    """Encrypt OAuth token for storage (simplified - use proper encryption in production)."""
    # In production, use Fernet or similar for proper encryption
    from cryptography.fernet import Fernet
    
    # Generate a key from secret key (in production, use separate encryption key)
    import hashlib
    key = hashlib.sha256(settings.secret_key.encode()).digest()
    import base64
    fernet_key = base64.urlsafe_b64encode(key)
    f = Fernet(fernet_key)
    
    return f.encrypt(token.encode()).decode()


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt OAuth token."""
    from cryptography.fernet import Fernet
    import hashlib
    import base64
    
    key = hashlib.sha256(settings.secret_key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key)
    f = Fernet(fernet_key)
    
    return f.decrypt(encrypted_token.encode()).decode()
