"""Schedule API routes for scheduled emails."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from app.models.database import get_db_session, User, ScheduledEmail
from app.api.schemas import ScheduleCreate, ScheduleResponse, MessageResponse
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


@router.post("/", response_model=ScheduleResponse)
async def schedule_email(
    schedule_data: ScheduleCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Schedule an email to be sent later."""
    scheduled = ScheduledEmail(
        user_id=user.id,
        recipients=schedule_data.recipients,
        subject=schedule_data.subject,
        body=schedule_data.body,
        scheduled_at=schedule_data.scheduled_at,
        timezone=schedule_data.timezone,
        is_recurring=schedule_data.is_recurring,
        recurring_pattern=schedule_data.recurring_pattern
    )
    
    db.add(scheduled)
    db.commit()
    db.refresh(scheduled)
    
    return scheduled


@router.get("/", response_model=List[ScheduleResponse])
async def list_scheduled(
    request: Request,
    pending_only: bool = True,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """List all scheduled emails."""
    query = db.query(ScheduledEmail).filter(
        ScheduledEmail.user_id == user.id
    )
    
    if pending_only:
        query = query.filter(ScheduledEmail.is_sent == False)
    
    scheduled = query.order_by(ScheduledEmail.scheduled_at.asc()).all()
    return scheduled


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_scheduled(
    schedule_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get a specific scheduled email."""
    scheduled = db.query(ScheduledEmail).filter(
        ScheduledEmail.id == schedule_id,
        ScheduledEmail.user_id == user.id
    ).first()
    
    if not scheduled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled email not found"
        )
    
    return scheduled


@router.delete("/{schedule_id}")
async def cancel_scheduled(
    schedule_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Cancel a scheduled email."""
    scheduled = db.query(ScheduledEmail).filter(
        ScheduledEmail.id == schedule_id,
        ScheduledEmail.user_id == user.id
    ).first()
    
    if not scheduled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled email not found"
        )
    
    db.delete(scheduled)
    db.commit()
    
    return MessageResponse(message="Scheduled email cancelled")


@router.post("/process")
async def process_scheduled(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Process and send due scheduled emails (called by cron/background task)."""
    from app.services.gmail_service import GmailService
    from app.utils.auth import decrypt_token
    
    now = datetime.utcnow()
    
    # Get due scheduled emails
    due_emails = db.query(ScheduledEmail).filter(
        ScheduledEmail.user_id == user.id,
        ScheduledEmail.is_sent == False,
        ScheduledEmail.scheduled_at <= now
    ).all()
    
    sent_count = 0
    failed_count = 0
    
    for scheduled in due_emails:
        try:
            # Get user's access token
            access_token = decrypt_token(user.access_token)
            gmail = GmailService(access_token=access_token)
            
            # Send the email
            gmail.send_email(
                to=scheduled.recipients,
                subject=scheduled.subject,
                body=scheduled.body
            )
            
            # Mark as sent
            scheduled.is_sent = True
            sent_count += 1
            
            # Handle recurring
            if scheduled.is_recurring and scheduled.recurring_pattern:
                # Create next occurrence
                next_time = scheduled.scheduled_at
                
                if scheduled.recurring_pattern == 'daily':
                    next_time += timedelta(days=1)
                elif scheduled.recurring_pattern == 'weekly':
                    next_time += timedelta(weeks=1)
                elif scheduled.recurring_pattern == 'monthly':
                    next_time += timedelta(days=30)
                
                # Create new scheduled email
                new_scheduled = ScheduledEmail(
                    user_id=user.id,
                    recipients=scheduled.recipients,
                    subject=scheduled.subject,
                    body=scheduled.body,
                    scheduled_at=next_time,
                    timezone=scheduled.timezone,
                    is_recurring=True,
                    recurring_pattern=scheduled.recurring_pattern
                )
                db.add(new_scheduled)
            
        except Exception as e:
            failed_count += 1
            print(f"Failed to send scheduled email {scheduled.id}: {str(e)}")
    
    db.commit()
    
    return {
        "message": f"Processed {len(due_emails)} scheduled emails",
        "sent": sent_count,
        "failed": failed_count
    }
