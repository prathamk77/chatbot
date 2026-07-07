from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json

Base = declarative_base()


class User(Base):
    """User model for storing user information and OAuth tokens."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255))
    picture = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # OAuth tokens (encrypted in production)
    access_token = Column(Text)
    refresh_token = Column(Text)
    token_expiry = Column(DateTime)
    
    # Relationships
    emails = relationship("Email", back_populates="user", cascade="all, delete-orphan")
    drafts = relationship("Draft", back_populates="user", cascade="all, delete-orphan")
    scheduled_emails = relationship("ScheduledEmail", back_populates="user", cascade="all, delete-orphan")
    templates = relationship("Template", back_populates="user", cascade="all, delete-orphan")
    contacts = relationship("Contact", back_populates="user", cascade="all, delete-orphan")
    analytics = relationship("Analytics", back_populates="user", uselist=False, cascade="all, delete-orphan")


class Email(Base):
    """Email model for storing sent/received emails."""
    __tablename__ = "emails"
    
    id = Column(Integer, primary_key=True, index=True)
    gmail_id = Column(String(255), unique=True, index=True)  # Gmail's message ID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Email fields
    subject = Column(String(500))
    sender = Column(String(255))
    recipients = Column(JSON)  # List of recipient emails
    cc = Column(JSON)
    bcc = Column(JSON)
    body = Column(Text)
    html_body = Column(Text)
    
    # Email metadata
    thread_id = Column(String(255))
    labels = Column(JSON)  # Gmail labels
    attachments = Column(JSON)
    
    # Status
    is_read = Column(Boolean, default=False)
    is_starred = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)
    is_draft = Column(Boolean, default=False)
    
    # AI metadata
    sentiment = Column(String(50))  # positive, negative, neutral
    category = Column(String(100))  # work, personal, spam, etc.
    summary = Column(Text)
    action_items = Column(JSON)
    
    # Timestamps
    received_at = Column(DateTime)
    sent_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="emails")
    follow_ups = relationship("FollowUp", back_populates="email", cascade="all, delete-orphan")


class Draft(Base):
    """Draft model for storing email drafts."""
    __tablename__ = "drafts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    gmail_draft_id = Column(String(255))  # Gmail's draft ID
    
    # Email fields
    subject = Column(String(500))
    recipients = Column(String(255))
    cc = Column(String(255))
    bcc = Column(String(255))
    body = Column(Text)
    
    # AI generation info
    prompt = Column(Text)
    tone = Column(String(50))
    template_id = Column(Integer, ForeignKey("templates.id"))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="drafts")
    template = relationship("Template", back_populates="drafts")


class ScheduledEmail(Base):
    """Scheduled email model for storing emails to be sent later."""
    __tablename__ = "scheduled_emails"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Email fields
    subject = Column(String(500))
    recipients = Column(String(255))
    body = Column(Text)
    
    # Schedule info
    scheduled_at = Column(DateTime, nullable=False)
    timezone = Column(String(50), default="UTC")
    is_recurring = Column(Boolean, default=False)
    recurring_pattern = Column(String(50))  # daily, weekly, monthly
    is_sent = Column(Boolean, default=False)
    
    # Follow-up settings
    is_follow_up = Column(Boolean, default=False)
    follow_up_interval_days = Column(Integer)
    original_email_id = Column(Integer, ForeignKey("emails.id"))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="scheduled_emails")
    original_email = relationship("Email", backref="scheduled_followups")


class Template(Base):
    """Email template model for storing reusable email templates."""
    __tablename__ = "templates"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Template fields
    name = Column(String(255), nullable=False)
    subject = Column(String(500))
    body = Column(Text, nullable=False)
    category = Column(String(100))  # business, followup, proposal, etc.
    tone = Column(String(50))
    is_builtin = Column(Boolean, default=False)  # Built-in vs user-created
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="templates")
    drafts = relationship("Draft", back_populates="template")


class Contact(Base):
    """Contact model for storing email contacts."""
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Contact fields
    email = Column(String(255), nullable=False)
    name = Column(String(255))
    company = Column(String(255))
    phone = Column(String(50))
    notes = Column(Text)
    
    # AI-generated metadata
    last_interaction = Column(DateTime)
    interaction_count = Column(Integer, default=0)
    sentiment_score = Column(Integer, default=0)  # -100 to 100
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="contacts")
    
    __table_args__ = (
        # Unique constraint for user + email combination
        {'sqlite_autoincrement': True}
    )


class FollowUp(Base):
    """Follow-up model for tracking automatic follow-ups."""
    __tablename__ = "follow_ups"
    
    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Follow-up settings
    interval_days = Column(Integer, nullable=False)
    max_follow_ups = Column(Integer, default=3)
    follow_up_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Last follow-up info
    last_follow_up_at = Column(DateTime)
    next_follow_up_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    email = relationship("Email", back_populates="follow_ups")


class Analytics(Base):
    """Analytics model for storing email statistics."""
    __tablename__ = "analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Statistics
    total_emails_sent = Column(Integer, default=0)
    total_emails_received = Column(Integer, default=0)
    total_drafts = Column(Integer, default=0)
    total_scheduled = Column(Integer, default=0)
    
    # Rates
    reply_rate = Column(Integer, default=0)  # Percentage
    avg_response_time_hours = Column(Integer, default=0)
    
    # AI usage
    ai_generations = Column(Integer, default=0)
    ai_improvements = Column(Integer, default=0)
    
    # Most active contacts (JSON array of contact IDs)
    top_contacts = Column(JSON, default=list)
    
    # Top templates (JSON array of template IDs)
    top_templates = Column(JSON, default=list)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="analytics")


# Create engine and session
def get_engine(database_url: str = None):
    """Create database engine."""
    from app.utils.config import settings
    db_url = database_url or settings.database_url
    
    # For SQLite, we need connect_args for thread safety
    if db_url.startswith("sqlite"):
        return create_engine(db_url, connect_args={"check_same_thread": False})
    return create_engine(db_url)


def get_db_session():
    """Get database session."""
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def init_db():
    """Initialize database tables."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
