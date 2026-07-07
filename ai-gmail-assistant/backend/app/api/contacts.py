"""Contacts API routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List

from app.models.database import get_db_session, User, Contact
from app.api.schemas import ContactCreate, ContactResponse, MessageResponse
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


@router.post("/", response_model=ContactResponse)
async def create_contact(
    contact_data: ContactCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Create a new contact."""
    # Check if contact already exists
    existing = db.query(Contact).filter(
        Contact.email == contact_data.email,
        Contact.user_id == user.id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contact with this email already exists"
        )
    
    contact = Contact(
        user_id=user.id,
        email=contact_data.email,
        name=contact_data.name,
        company=contact_data.company,
        phone=contact_data.phone,
        notes=contact_data.notes
    )
    
    db.add(contact)
    db.commit()
    db.refresh(contact)
    
    return contact


@router.get("/", response_model=List[ContactResponse])
async def list_contacts(
    request: Request,
    search: str = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """List all contacts."""
    query = db.query(Contact).filter(Contact.user_id == user.id)
    
    if search:
        query = query.filter(
            (Contact.name.ilike(f"%{search}%")) |
            (Contact.email.ilike(f"%{search}%")) |
            (Contact.company.ilike(f"%{search}%"))
        )
    
    contacts = query.order_by(Contact.created_at.desc()).all()
    return contacts


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get a specific contact."""
    contact = db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.user_id == user.id
    ).first()
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    return contact


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    contact_data: ContactCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Update a contact."""
    contact = db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.user_id == user.id
    ).first()
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    contact.name = contact_data.name
    contact.company = contact_data.company
    contact.phone = contact_data.phone
    contact.notes = contact_data.notes
    
    db.commit()
    db.refresh(contact)
    
    return contact


@router.delete("/{contact_id}")
async def delete_contact(
    contact_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Delete a contact."""
    contact = db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.user_id == user.id
    ).first()
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    db.delete(contact)
    db.commit()
    
    return MessageResponse(message="Contact deleted successfully")


@router.post("/import")
async def import_contacts(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Import contacts from CSV/JSON."""
    try:
        body = await request.json()
        contacts_data = body.get('contacts', [])
        
        imported_count = 0
        skipped_count = 0
        
        for contact_data in contacts_data:
            # Check if exists
            existing = db.query(Contact).filter(
                Contact.email == contact_data.get('email'),
                Contact.user_id == user.id
            ).first()
            
            if existing:
                skipped_count += 1
                continue
            
            contact = Contact(
                user_id=user.id,
                email=contact_data.get('email'),
                name=contact_data.get('name'),
                company=contact_data.get('company'),
                phone=contact_data.get('phone'),
                notes=contact_data.get('notes')
            )
            db.add(contact)
            imported_count += 1
        
        db.commit()
        
        return {
            "message": f"Imported {imported_count} contacts",
            "skipped": skipped_count,
            "imported": imported_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import contacts: {str(e)}"
        )
