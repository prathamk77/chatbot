"""AI API routes for email generation and analysis."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List

from app.models.database import get_db_session, User, Analytics
from app.services.ollama_service import ollama_service
from app.api.schemas import (
    AIImproveRequest, AISummarizeRequest, AITranslateRequest,
    AIRewriteRequest, AIReplySuggestion, MessageResponse
)
from app.utils.auth import decode_access_token

router = APIRouter()


def get_db():
    """Database session dependency."""
    db = get_db_session()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Get current authenticated user."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    token = auth_header.split(" ")[1]
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    email = payload.get("sub")
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.post("/improve")
async def improve_grammar(
    request_data: AIImproveRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Improve grammar and clarity of text."""
    try:
        improved = await ollama_service.improve_grammar(request_data.text)
        
        # Update analytics
        analytics = db.query(Analytics).filter(Analytics.user_id == user.id).first()
        if analytics:
            analytics.ai_improvements += 1
        else:
            analytics = Analytics(user_id=user.id, ai_improvements=1)
            db.add(analytics)
        db.commit()
        
        return {"original": request_data.text, "improved": improved}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to improve text: {str(e)}"
        )


@router.post("/summarize")
async def summarize(
    request_data: AISummarizeRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Summarize long text."""
    try:
        summary = await ollama_service.summarize_email(request_data.text)
        return {"summary": summary}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to summarize: {str(e)}"
        )


@router.post("/translate")
async def translate(
    request_data: AITranslateRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Translate text to another language."""
    try:
        translated = await ollama_service.translate_email(
            request_data.text,
            request_data.target_language
        )
        return {
            "original": request_data.text,
            "translated": translated,
            "language": request_data.target_language
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to translate: {str(e)}"
        )


@router.post("/rewrite")
async def rewrite(
    request_data: AIRewriteRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Rewrite text with different tone."""
    try:
        rewritten = await ollama_service.rewrite_email(
            request_data.text,
            request_data.tone
        )
        return {
            "original": request_data.text,
            "rewritten": rewritten,
            "tone": request_data.tone
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rewrite: {str(e)}"
        )


@router.post("/suggest-reply")
async def suggest_reply(
    request_data: AIReplySuggestion,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Suggest a reply to an email."""
    try:
        reply = await ollama_service.suggest_reply(
            request_data.email_content,
            request_data.tone
        )
        return {"suggested_reply": reply}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to suggest reply: {str(e)}"
        )


@router.post("/sentiment")
async def analyze_sentiment(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Analyze sentiment of text."""
    try:
        body = await request.json()
        text = body.get('text', '')
        
        sentiment = await ollama_service.detect_sentiment(text)
        return {"sentiment": sentiment}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze sentiment: {str(e)}"
        )


@router.post("/action-items")
async def extract_action_items(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Extract action items from text."""
    try:
        body = await request.json()
        text = body.get('text', '')
        
        items = await ollama_service.extract_action_items(text)
        return {"action_items": items}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract action items: {str(e)}"
        )


@router.post("/categorize")
async def categorize(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Categorize email content."""
    try:
        body = await request.json()
        text = body.get('text', '')
        
        category = await ollama_service.categorize_email(text)
        return {"category": category}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to categorize: {str(e)}"
        )


@router.post("/spam-check")
async def check_spam(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Check if content is spam."""
    try:
        body = await request.json()
        text = body.get('text', '')
        
        is_spam = await ollama_service.detect_spam(text)
        return {"is_spam": is_spam}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check spam: {str(e)}"
        )


@router.post("/subject-lines")
async def generate_subject_lines(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Generate subject line options."""
    try:
        body = await request.json()
        text = body.get('text', '')
        count = body.get('count', 5)
        
        subjects = await ollama_service.generate_subject_lines(text, count)
        return {"subject_lines": subjects}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate subject lines: {str(e)}"
        )


@router.get("/models")
async def list_models(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """List available Ollama models."""
    try:
        models = await ollama_service.list_models()
        return {"models": models}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list models: {str(e)}"
        )


@router.get("/status")
async def ollama_status(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Check Ollama connection status."""
    try:
        is_connected = await ollama_service.check_connection()
        return {
            "connected": is_connected,
            "model": ollama_service.model,
            "base_url": ollama_service.base_url
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check status: {str(e)}"
        )
