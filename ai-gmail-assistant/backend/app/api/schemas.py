"""Pydantic schemas for API request/response validation."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_email: Optional[str] = None


class TokenData(BaseModel):
    email: Optional[str] = None


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    id: int
    picture: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Email Schemas
class EmailBase(BaseModel):
    subject: Optional[str] = None
    recipients: str
    body: str
    cc: Optional[str] = None
    bcc: Optional[str] = None


class EmailSend(EmailBase):
    is_html: bool = False
    in_reply_to: Optional[str] = None


class EmailGenerate(BaseModel):
    recipient: EmailStr
    prompt: str
    subject_hint: Optional[str] = None
    tone: str = "Professional"
    context: Optional[str] = None


class EmailResponse(BaseModel):
    id: int
    gmail_id: Optional[str] = None
    subject: Optional[str] = None
    sender: Optional[str] = None
    recipients: Optional[Any] = None
    body: Optional[str] = None
    is_read: bool = False
    is_starred: bool = False
    labels: Optional[List[str]] = None
    received_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class EmailListResponse(BaseModel):
    emails: List[EmailResponse]
    total: int


# Draft Schemas
class DraftCreate(BaseModel):
    recipients: str
    subject: Optional[str] = None
    body: str
    prompt: Optional[str] = None
    tone: Optional[str] = None


class DraftResponse(BaseModel):
    id: int
    subject: Optional[str] = None
    recipients: str
    body: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Scheduled Email Schemas
class ScheduleCreate(BaseModel):
    recipients: str
    subject: str
    body: str
    scheduled_at: datetime
    timezone: str = "UTC"
    is_recurring: bool = False
    recurring_pattern: Optional[str] = None


class ScheduleResponse(BaseModel):
    id: int
    subject: str
    recipients: str
    scheduled_at: datetime
    is_sent: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Template Schemas
class TemplateBase(BaseModel):
    name: str
    subject: Optional[str] = None
    body: str
    category: Optional[str] = None
    tone: Optional[str] = None


class TemplateCreate(TemplateBase):
    pass


class TemplateResponse(TemplateBase):
    id: int
    is_builtin: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True


# Contact Schemas
class ContactBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None


class ContactCreate(ContactBase):
    pass


class ContactResponse(ContactBase):
    id: int
    last_interaction: Optional[datetime] = None
    interaction_count: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True


# Analytics Schemas
class AnalyticsResponse(BaseModel):
    total_emails_sent: int = 0
    total_emails_received: int = 0
    total_drafts: int = 0
    total_scheduled: int = 0
    reply_rate: int = 0
    avg_response_time_hours: int = 0
    ai_generations: int = 0
    top_contacts: List[Dict] = []
    top_templates: List[Dict] = []


# AI Schemas
class AIImproveRequest(BaseModel):
    text: str


class AISummarizeRequest(BaseModel):
    text: str


class AITranslateRequest(BaseModel):
    text: str
    target_language: str


class AIRewriteRequest(BaseModel):
    text: str
    tone: str = "Professional"


class AIReplySuggestion(BaseModel):
    email_content: str
    tone: str = "Professional"


# Follow-up Schema
class FollowUpCreate(BaseModel):
    email_id: int
    interval_days: int = 2
    max_follow_ups: int = 3


class FollowUpResponse(BaseModel):
    id: int
    email_id: int
    interval_days: int
    follow_up_count: int
    is_active: bool
    next_follow_up_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Generic Response
class MessageResponse(BaseModel):
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    detail: str
    success: bool = False
