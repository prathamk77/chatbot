"""Email API routes for Gmail operations."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models.database import get_db_session, User, Email as EmailModel, Draft, FollowUp
from app.services.gmail_service import GmailService
from app.services.ollama_service import ollama_service
from app.api.schemas import (
    EmailSend, EmailGenerate, EmailResponse, EmailListResponse,
    DraftCreate, DraftResponse, MessageResponse, FollowUpCreate, FollowUpResponse
)
from app.utils.auth import decode_access_token, decrypt_token
from app.utils.config import settings

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


@router.get("/inbox")
async def list_emails(
    request: Request,
    max_results: int = 20,
    query: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """List emails from Gmail inbox."""
    try:
        access_token = decrypt_token(user.access_token)
        gmail = GmailService(access_token=access_token)
        
        emails = gmail.list_emails(max_results=max_results, query=query)
        
        # Save to database
        for email_data in emails:
            existing = db.query(EmailModel).filter(
                EmailModel.gmail_id == email_data['id']
            ).first()
            
            if not existing:
                email = EmailModel(
                    gmail_id=email_data['id'],
                    user_id=user.id,
                    subject=email_data.get('subject'),
                    sender=email_data.get('sender'),
                    recipients=[email_data.get('to', '')],
                    body='',
                    is_read=email_data.get('is_read', False),
                    is_starred=email_data.get('is_starred', False),
                    labels=email_data.get('labels', []),
                    thread_id=email_data.get('thread_id')
                )
                db.add(email)
        
        db.commit()
        
        # Get saved emails from DB
        db_emails = db.query(EmailModel).filter(
            EmailModel.user_id == user.id
        ).order_by(EmailModel.created_at.desc()).limit(max_results).all()
        
        return {
            "emails": db_emails,
            "total": len(db_emails)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch emails: {str(e)}"
        )


@router.get("/{email_id}")
async def get_email(
    email_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get full email details."""
    try:
        access_token = decrypt_token(user.access_token)
        gmail = GmailService(access_token=access_token)
        
        email_data = gmail.get_email(email_id)
        
        # Save/update in database
        email = db.query(EmailModel).filter(
            EmailModel.gmail_id == email_id
        ).first()
        
        if not email:
            email = EmailModel(
                gmail_id=email_data['id'],
                user_id=user.id,
                subject=email_data.get('subject'),
                sender=email_data.get('sender'),
                recipients=[email_data.get('to', '')],
                body=email_data.get('body', ''),
                is_read=email_data.get('is_read', False),
                is_starred=email_data.get('is_starred', False),
                labels=email_data.get('labels', []),
                thread_id=email_data.get('thread_id')
            )
            db.add(email)
        else:
            email.body = email_data.get('body', email.body)
            email.is_read = email_data.get('is_read', email.is_read)
        
        db.commit()
        db.refresh(email)
        
        return email
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get email: {str(e)}"
        )


@router.post("/send")
async def send_email(
    email_data: EmailSend,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Send an email via Gmail."""
    try:
        access_token = decrypt_token(user.access_token)
        gmail = GmailService(access_token=access_token)
        
        result = gmail.send_email(
            to=email_data.recipients,
            subject=email_data.subject or "(No subject)",
            body=email_data.body,
            html=email_data.is_html,
            cc=email_data.cc,
            bcc=email_data.bcc,
            in_reply_to=email_data.in_reply_to
        )
        
        # Save to database
        email = EmailModel(
            gmail_id=result['id'],
            user_id=user.id,
            subject=email_data.subject,
            sender=user.email,
            recipients=[email_data.recipients],
            body=email_data.body,
            is_sent=True,
            thread_id=result.get('thread_id'),
            sent_at=datetime.utcnow()
        )
        db.add(email)
        
        # Update analytics
        from app.models.database import Analytics
        analytics = db.query(Analytics).filter(Analytics.user_id == user.id).first()
        if analytics:
            analytics.total_emails_sent += 1
        else:
            analytics = Analytics(user_id=user.id, total_emails_sent=1)
            db.add(analytics)
        
        db.commit()
        
        return MessageResponse(message="Email sent successfully")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )


@router.post("/generate")
async def generate_email(
    gen_data: EmailGenerate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Generate email content using AI."""
    try:
        # Call Ollama to generate email
        generated = await ollama_service.generate_email(
            prompt=gen_data.prompt,
            recipient=gen_data.recipient,
            subject_hint=gen_data.subject_hint,
            tone=gen_data.tone,
            context=gen_data.context
        )
        
        # Update AI usage analytics
        from app.models.database import Analytics
        analytics = db.query(Analytics).filter(Analytics.user_id == user.id).first()
        if analytics:
            analytics.ai_generations += 1
        else:
            analytics = Analytics(user_id=user.id, ai_generations=1)
            db.add(analytics)
        
        db.commit()
        
        return generated
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate email: {str(e)}"
        )


@router.post("/draft")
async def create_draft(
    draft_data: DraftCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Save a draft email."""
    try:
        access_token = decrypt_token(user.access_token)
        gmail = GmailService(access_token=access_token)
        
        # Create draft in Gmail
        gmail_draft = gmail.create_draft(
            to=draft_data.recipients,
            subject=draft_data.subject or "(No subject)",
            body=draft_data.body
        )
        
        # Save to database
        draft = Draft(
            user_id=user.id,
            gmail_draft_id=gmail_draft['id'],
            subject=draft_data.subject,
            recipients=draft_data.recipients,
            body=draft_data.body,
            prompt=draft_data.prompt,
            tone=draft_data.tone
        )
        db.add(draft)
        
        db.commit()
        db.refresh(draft)
        
        return draft
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create draft: {str(e)}"
        )


@router.get("/drafts")
async def list_drafts(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """List all drafts."""
    drafts = db.query(Draft).filter(
        Draft.user_id == user.id
    ).order_by(Draft.created_at.desc()).all()
    
    return {"drafts": drafts, "total": len(drafts)}


@router.delete("/{email_id}")
async def delete_email(
    email_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Delete an email."""
    try:
        access_token = decrypt_token(user.access_token)
        gmail = GmailService(access_token=access_token)
        
        gmail.delete_email(email_id)
        
        # Remove from database
        db.query(EmailModel).filter(
            EmailModel.gmail_id == email_id,
            EmailModel.user_id == user.id
        ).delete()
        
        db.commit()
        
        return MessageResponse(message="Email deleted successfully")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete email: {str(e)}"
        )


@router.post("/{email_id}/star")
async def star_email(
    email_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Star/unstar an email."""
    try:
        access_token = decrypt_token(user.access_token)
        gmail = GmailService(access_token=access_token)
        
        # Get current state
        email_data = gmail.get_email(email_id)
        is_starred = email_data.get('is_starred', False)
        
        if is_starred:
            gmail.unstar_email(email_id)
        else:
            gmail.star_email(email_id)
        
        # Update in database
        email = db.query(EmailModel).filter(
            EmailModel.gmail_id == email_id
        ).first()
        
        if email:
            email.is_starred = not is_starred
            db.commit()
        
        return MessageResponse(
            message=f"Email {'unstarred' if is_starred else 'starred'} successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update email: {str(e)}"
        )


@router.post("/{email_id}/read")
async def mark_read(
    email_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Mark email as read/unread."""
    try:
        access_token = decrypt_token(user.access_token)
        gmail = GmailService(access_token=access_token)
        
        # Get current state
        email_data = gmail.get_email(email_id)
        is_read = email_data.get('is_read', False)
        
        if is_read:
            gmail.mark_as_unread(email_id)
        else:
            gmail.mark_as_read(email_id)
        
        # Update in database
        email = db.query(EmailModel).filter(
            EmailModel.gmail_id == email_id
        ).first()
        
        if email:
            email.is_read = not is_read
            db.commit()
        
        return MessageResponse(
            message=f"Email marked as {'unread' if is_read else 'read'}"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update email: {str(e)}"
        )


@router.post("/follow-up", response_model=FollowUpResponse)
async def create_follow_up(
    follow_up_data: FollowUpCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Set up automatic follow-up for an email."""
    from datetime import timedelta
    
    email = db.query(EmailModel).filter(
        EmailModel.id == follow_up_data.email_id,
        EmailModel.user_id == user.id
    ).first()
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )
    
    follow_up = FollowUp(
        email_id=follow_up_data.email_id,
        user_id=user.id,
        interval_days=follow_up_data.interval_days,
        max_follow_ups=follow_up_data.max_follow_ups,
        next_follow_up_at=datetime.utcnow() + timedelta(days=follow_up_data.interval_days)
    )
    
    db.add(follow_up)
    db.commit()
    db.refresh(follow_up)
    
    return follow_up
