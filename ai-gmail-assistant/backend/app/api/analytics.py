"""Analytics API routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session, aliased
from sqlalchemy import func
from typing import List
from datetime import datetime, timedelta

from app.models.database import get_db_session, User, Analytics, Email, Draft, ScheduledEmail, Contact
from app.api.schemas import AnalyticsResponse
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


@router.get("/", response_model=AnalyticsResponse)
async def get_analytics(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get user analytics dashboard data."""
    # Get or create analytics record
    analytics = db.query(Analytics).filter(Analytics.user_id == user.id).first()
    
    if not analytics:
        analytics = Analytics(user_id=user.id)
        db.add(analytics)
        db.commit()
        db.refresh(analytics)
    
    # Calculate real-time stats
    total_sent = db.query(Email).filter(
        Email.user_id == user.id,
        Email.is_sent == True
    ).count()
    
    total_received = db.query(Email).filter(
        Email.user_id == user.id,
        Email.is_sent == False
    ).count()
    
    total_drafts = db.query(Draft).filter(
        Draft.user_id == user.id
    ).count()
    
    total_scheduled = db.query(ScheduledEmail).filter(
        ScheduledEmail.user_id == user.id,
        ScheduledEmail.is_sent == False
    ).count()
    
    # Update analytics
    analytics.total_emails_sent = total_sent
    analytics.total_emails_received = total_received
    analytics.total_drafts = total_drafts
    analytics.total_scheduled = total_scheduled
    
    # Calculate reply rate (simplified)
    if total_sent > 0:
        # Count emails that have replies (same thread)
        replied_count = db.query(Email).filter(
            Email.user_id == user.id,
            Email.thread_id != None
        ).distinct(Email.thread_id).count()
        analytics.reply_rate = min(100, int((replied_count / total_sent) * 100))
    
    # Get top contacts
    top_contacts = db.query(
        Contact.email,
        Contact.name,
        Contact.interaction_count
    ).filter(
        Contact.user_id == user.id
    ).order_by(
        Contact.interaction_count.desc()
    ).limit(5).all()
    
    analytics.top_contacts = [
        {"email": c.email, "name": c.name, "interactions": c.interaction_count}
        for c in top_contacts
    ]
    
    db.commit()
    
    return analytics


@router.get("/emails/sent")
async def get_sent_emails_count(
    request: Request,
    days: int = 30,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get count of sent emails in the last N days."""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    count = db.query(Email).filter(
        Email.user_id == user.id,
        Email.is_sent == True,
        Email.created_at >= cutoff_date
    ).count()
    
    return {"count": count, "days": days}


@router.get("/emails/received")
async def get_received_emails_count(
    request: Request,
    days: int = 30,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get count of received emails in the last N days."""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    count = db.query(Email).filter(
        Email.user_id == user.id,
        Email.is_sent == False,
        Email.created_at >= cutoff_date
    ).count()
    
    return {"count": count, "days": days}


@router.get("/activity")
async def get_activity_summary(
    request: Request,
    days: int = 7,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get activity summary for the last N days."""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Emails sent per day
    sent_per_day = db.query(
        func.date(Email.created_at).label('date'),
        func.count(Email.id).label('count')
    ).filter(
        Email.user_id == user.id,
        Email.is_sent == True,
        Email.created_at >= cutoff_date
    ).group_by(func.date(Email.created_at)).all()
    
    # Drafts created per day
    drafts_per_day = db.query(
        func.date(Draft.created_at).label('date'),
        func.count(Draft.id).label('count')
    ).filter(
        Draft.user_id == user.id,
        Draft.created_at >= cutoff_date
    ).group_by(func.date(Draft.created_at)).all()
    
    return {
        "sent_per_day": [{"date": str(d.date), "count": d.count} for d in sent_per_day],
        "drafts_per_day": [{"date": str(d.date), "count": d.count} for d in drafts_per_day]
    }


@router.get("/contacts/stats")
async def get_contacts_stats(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get contacts statistics."""
    total_contacts = db.query(Contact).filter(
        Contact.user_id == user.id
    ).count()
    
    contacts_with_company = db.query(Contact).filter(
        Contact.user_id == user.id,
        Contact.company != None
    ).count()
    
    return {
        "total_contacts": total_contacts,
        "with_company": contacts_with_company,
        "without_company": total_contacts - contacts_with_company
    }
