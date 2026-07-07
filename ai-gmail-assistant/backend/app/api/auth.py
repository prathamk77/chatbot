"""Authentication API routes for Google OAuth."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
import httpx

from app.models.database import get_db_session, User
from app.services.gmail_service import GmailService
from app.utils.auth import create_access_token, encrypt_token
from app.api.schemas import Token, MessageResponse
from app.utils.config import settings

router = APIRouter()


def get_db():
    """Dependency for database session."""
    db = get_db_session()
    try:
        yield db
    finally:
        db.close()


@router.get("/login")
async def login(request: Request):
    """Initiate Google OAuth login flow."""
    try:
        auth_url = GmailService.get_authorization_url()
        return {"authorization_url": auth_url}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate authorization URL: {str(e)}"
        )


@router.get("/callback")
async def oauth_callback(
    request: Request,
    code: str,
    db: Session = Depends(get_db)
):
    """Handle OAuth callback from Google."""
    try:
        # Exchange code for tokens
        token_info = GmailService.exchange_code_for_tokens(code)
        
        if not token_info.get('access_token'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to obtain access token"
            )
        
        # Check if user exists
        user = db.query(User).filter(
            User.email == token_info['email']
        ).first()
        
        if user:
            # Update existing user's tokens
            user.access_token = encrypt_token(token_info['access_token'])
            if token_info.get('refresh_token'):
                user.refresh_token = encrypt_token(token_info['refresh_token'])
            user.name = token_info.get('name') or user.name
            user.picture = token_info.get('picture') or user.picture
        else:
            # Create new user
            user = User(
                email=token_info['email'],
                name=token_info.get('name'),
                picture=token_info.get('picture'),
                access_token=encrypt_token(token_info['access_token']),
                refresh_token=encrypt_token(token_info['refresh_token']) if token_info.get('refresh_token') else None
            )
            db.add(user)
        
        db.commit()
        db.refresh(user)
        
        # Create JWT token for our API
        access_token = create_access_token(data={"sub": user.email})
        
        # Return success response with token (frontend will handle redirect)
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_email": user.email,
            "user_name": user.name,
            "user_picture": user.picture
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth callback failed: {str(e)}"
        )


@router.post("/logout")
async def logout(request: Request):
    """Logout user (client-side token removal)."""
    # In a real app, you might want to invalidate the token server-side
    return MessageResponse(message="Logged out successfully")


@router.get("/me")
async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get current authenticated user info."""
    # Get token from header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = auth_header.split(" ")[1]
    
    # Decode and validate token
    from app.utils.auth import decode_access_token
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Get user from database
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
        "created_at": user.created_at
    }


@router.get("/status")
async def auth_status(request: Request):
    """Check authentication status."""
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"authenticated": False}
    
    token = auth_header.split(" ")[1]
    
    from app.utils.auth import decode_access_token
    payload = decode_access_token(token)
    
    if not payload:
        return {"authenticated": False}
    
    return {
        "authenticated": True,
        "email": payload.get("sub")
    }
