"""Templates API routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List

from app.models.database import get_db_session, User, Template
from app.api.schemas import TemplateCreate, TemplateResponse, MessageResponse
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


@router.post("/", response_model=TemplateResponse)
async def create_template(
    template_data: TemplateCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Create a new email template."""
    template = Template(
        user_id=user.id,
        name=template_data.name,
        subject=template_data.subject,
        body=template_data.body,
        category=template_data.category,
        tone=template_data.tone
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return template


@router.get("/", response_model=List[TemplateResponse])
async def list_templates(
    request: Request,
    category: str = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """List all templates (user + built-in)."""
    query = db.query(Template).filter(
        (Template.user_id == user.id) | (Template.is_builtin == True)
    )
    
    if category:
        query = query.filter(Template.category == category)
    
    templates = query.order_by(Template.created_at.desc()).all()
    return templates


@router.get("/builtin", response_model=List[TemplateResponse])
async def list_builtin_templates(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """List built-in templates."""
    # Create default templates if none exist
    builtin_count = db.query(Template).filter(Template.is_builtin == True).count()
    
    if builtin_count == 0:
        default_templates = [
            {
                "name": "Business Proposal",
                "subject": "Proposal for {{service}}",
                "body": "Dear {{name}},\n\nI hope this email finds you well. I am writing to propose...\n\nBest regards,\n{{signature}}",
                "category": "business",
                "tone": "Professional"
            },
            {
                "name": "Cold Outreach",
                "subject": "Quick question about {{company}}",
                "body": "Hi {{name}},\n\nI came across {{company}} and was impressed by...\n\nWould love to connect.\n\nBest,\n{{signature}}",
                "category": "outreach",
                "tone": "Friendly"
            },
            {
                "name": "Follow-up",
                "subject": "Following up on our conversation",
                "body": "Hi {{name}},\n\nJust wanted to follow up on my previous email regarding...\n\nLooking forward to hearing from you.\n\nBest,\n{{signature}}",
                "category": "followup",
                "tone": "Professional"
            },
            {
                "name": "Meeting Request",
                "subject": "Meeting Request: {{topic}}",
                "body": "Dear {{name}},\n\nI would like to schedule a meeting to discuss...\n\nPlease let me know your availability.\n\nBest regards,\n{{signature}}",
                "category": "meeting",
                "tone": "Formal"
            },
            {
                "name": "Thank You",
                "subject": "Thank you!",
                "body": "Dear {{name}},\n\nI wanted to express my sincere gratitude for...\n\nThank you again for your support.\n\nBest regards,\n{{signature}}",
                "category": "thankyou",
                "tone": "Friendly"
            },
            {
                "name": "Invoice",
                "subject": "Invoice #{{number}} - {{service}}",
                "body": "Dear {{name}},\n\nPlease find attached the invoice for...\n\nPayment is due by {{date}}.\n\nThank you,\n{{signature}}",
                "category": "invoice",
                "tone": "Professional"
            },
            {
                "name": "Job Application",
                "subject": "Application for {{position}} - {{name}}",
                "body": "Dear Hiring Manager,\n\nI am writing to apply for the {{position}} role at {{company}}...\n\nI look forward to discussing my application further.\n\nBest regards,\n{{signature}}",
                "category": "job",
                "tone": "Formal"
            },
            {
                "name": "Support Response",
                "subject": "Re: Support Ticket #{{number}}",
                "body": "Dear {{name}},\n\nThank you for contacting support. Regarding your issue...\n\nPlease let us know if you need further assistance.\n\nBest regards,\n{{signature}}",
                "category": "support",
                "tone": "Friendly"
            }
        ]
        
        for tmpl in default_templates:
            builtin = Template(
                user_id=user.id,
                name=tmpl["name"],
                subject=tmpl["subject"],
                body=tmpl["body"],
                category=tmpl["category"],
                tone=tmpl["tone"],
                is_builtin=True
            )
            db.add(builtin)
        
        db.commit()
    
    templates = db.query(Template).filter(
        Template.is_builtin == True
    ).all()
    
    return templates


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get a specific template."""
    template = db.query(Template).filter(
        Template.id == template_id,
        (Template.user_id == user.id) | (Template.is_builtin == True)
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    return template


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int,
    template_data: TemplateCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Update a template."""
    template = db.query(Template).filter(
        Template.id == template_id,
        Template.user_id == user.id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    template.name = template_data.name
    template.subject = template_data.subject
    template.body = template_data.body
    template.category = template_data.category
    template.tone = template_data.tone
    
    db.commit()
    db.refresh(template)
    
    return template


@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Delete a template."""
    template = db.query(Template).filter(
        Template.id == template_id,
        Template.user_id == user.id,
        Template.is_builtin == False
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found or cannot delete built-in templates"
        )
    
    db.delete(template)
    db.commit()
    
    return MessageResponse(message="Template deleted successfully")
