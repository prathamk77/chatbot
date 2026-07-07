"""Gmail API service for email operations."""

import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional, Any
from datetime import datetime
import httpx
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.utils.config import settings


class GmailService:
    """Service for interacting with Gmail API."""
    
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/gmail.compose',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile'
    ]
    
    def __init__(self, access_token: str, refresh_token: Optional[str] = None):
        """Initialize Gmail service with OAuth tokens."""
        self.credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            scopes=self.SCOPES
        )
        self.service = build('gmail', 'v1', credentials=self.credentials)
    
    @classmethod
    def get_authorization_url(cls, redirect_uri: str = None) -> str:
        """Get OAuth authorization URL."""
        redirect_uri = redirect_uri or settings.google_redirect_uri
        
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [redirect_uri],
                }
            },
            scopes=cls.SCOPES,
            redirect_uri=redirect_uri
        )
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        return authorization_url
    
    @classmethod
    def exchange_code_for_tokens(cls, code: str, redirect_uri: str = None) -> Dict[str, Any]:
        """Exchange authorization code for tokens."""
        redirect_uri = redirect_uri or settings.google_redirect_uri
        
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [redirect_uri],
                }
            },
            scopes=cls.SCOPES,
            redirect_uri=redirect_uri
        )
        
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        return {
            'access_token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_expiry': credentials.expiry.isoformat() if credentials.expiry else None,
            'email': credentials.id_token.get('email') if credentials.id_token else None,
            'name': credentials.id_token.get('name') if credentials.id_token else None,
            'picture': credentials.id_token.get('picture') if credentials.id_token else None
        }
    
    def refresh_access_token(self) -> str:
        """Refresh the access token."""
        self.credentials.refresh(httpx.Client())
        return self.credentials.token
    
    def get_profile(self) -> Dict[str, Any]:
        """Get user's Gmail profile."""
        try:
            profile = self.service.users().getProfile(userId='me').execute()
            return {
                'email': profile['emailAddress'],
                'name': profile.get('displayName', ''),
                'total_messages': profile.get('messagesTotal', 0),
                'total_threads': profile.get('threadsTotal', 0)
            }
        except HttpError as error:
            raise Exception(f"Failed to get profile: {error}")
    
    def list_emails(self, max_results: int = 20, query: str = None, 
                    label_ids: List[str] = None) -> List[Dict[str, Any]]:
        """List emails from inbox."""
        try:
            request_params = {
                'userId': 'me',
                'maxResults': min(max_results, 500)
            }
            
            if query:
                request_params['q'] = query
            
            if label_ids:
                request_params['labelIds'] = label_ids
            
            response = self.service.users().messages().list(**request_params).execute()
            messages = response.get('messages', [])
            
            # Get full message details
            emails = []
            for msg in messages[:max_results]:
                try:
                    full_msg = self.service.users().messages().get(
                        userId='me', id=msg['id'], format='metadata',
                        metadataHeaders=['Subject', 'From', 'To', 'Date']
                    ).execute()
                    
                    emails.append(self._parse_message(full_msg))
                except Exception:
                    continue
            
            return emails
            
        except HttpError as error:
            raise Exception(f"Failed to list emails: {error}")
    
    def get_email(self, message_id: str) -> Dict[str, Any]:
        """Get full email details."""
        try:
            message = self.service.users().messages().get(
                userId='me', id=message_id, format='full'
            ).execute()
            return self._parse_message(message, full=True)
        except HttpError as error:
            raise Exception(f"Failed to get email: {error}")
    
    def send_email(self, to: str, subject: str, body: str, 
                   html: bool = False, cc: str = None, bcc: str = None,
                   in_reply_to: str = None) -> Dict[str, Any]:
        """Send an email."""
        try:
            message = MIMEMultipart("alternative")
            message['to'] = to
            message['subject'] = subject
            
            if cc:
                message['cc'] = cc
            if bcc:
                message['bcc'] = bcc
            if in_reply_to:
                message['In-Reply-To'] = in_reply_to
                message['References'] = in_reply_to
            
            # Add body
            if html:
                message.attach(MIMEText(body, 'html'))
            else:
                message.attach(MIMEText(body, 'plain'))
            
            # Encode and send
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            sent_message = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            return {
                'id': sent_message['id'],
                'thread_id': sent_message['threadId'],
                'status': 'sent'
            }
            
        except HttpError as error:
            raise Exception(f"Failed to send email: {error}")
    
    def create_draft(self, to: str, subject: str, body: str,
                     cc: str = None, bcc: str = None) -> Dict[str, Any]:
        """Create a draft email."""
        try:
            message = MIMEMultipart("alternative")
            message['to'] = to
            message['subject'] = subject
            
            if cc:
                message['cc'] = cc
            if bcc:
                message['bcc'] = bcc
            
            message.attach(MIMEText(body, 'plain'))
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            draft = self.service.users().drafts().create(
                userId='me',
                body={'message': {'raw': raw_message}}
            ).execute()
            
            return {
                'id': draft['id'],
                'message_id': draft['message']['id']
            }
            
        except HttpError as error:
            raise Exception(f"Failed to create draft: {error}")
    
    def delete_email(self, message_id: str) -> bool:
        """Delete an email."""
        try:
            self.service.users().messages().delete(
                userId='me', id=message_id
            ).execute()
            return True
        except HttpError as error:
            raise Exception(f"Failed to delete email: {error}")
    
    def archive_email(self, message_id: str) -> bool:
        """Archive an email (remove INBOX label)."""
        try:
            self.service.users().messages().modify(
                userId='me', id=message_id,
                body={'removeLabelIds': ['INBOX']}
            ).execute()
            return True
        except HttpError as error:
            raise Exception(f"Failed to archive email: {error}")
    
    def mark_as_read(self, message_id: str) -> bool:
        """Mark email as read."""
        try:
            self.service.users().messages().modify(
                userId='me', id=message_id,
                body={'addLabelIds': ['READ']}
            ).execute()
            return True
        except HttpError as error:
            raise Exception(f"Failed to mark as read: {error}")
    
    def mark_as_unread(self, message_id: str) -> bool:
        """Mark email as unread."""
        try:
            self.service.users().messages().modify(
                userId='me', id=message_id,
                body={'removeLabelIds': ['READ']}
            ).execute()
            return True
        except HttpError as error:
            raise Exception(f"Failed to mark as unread: {error}")
    
    def star_email(self, message_id: str) -> bool:
        """Star an email."""
        try:
            self.service.users().messages().modify(
                userId='me', id=message_id,
                body={'addLabelIds': ['STARRED']}
            ).execute()
            return True
        except HttpError as error:
            raise Exception(f"Failed to star email: {error}")
    
    def unstar_email(self, message_id: str) -> bool:
        """Unstar an email."""
        try:
            self.service.users().messages().modify(
                userId='me', id=message_id,
                body={'removeLabelIds': ['STARRED']}
            ).execute()
            return True
        except HttpError as error:
            raise Exception(f"Failed to unstar email: {error}")
    
    def search_emails(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """Search emails using Gmail search syntax."""
        return self.list_emails(max_results=max_results, query=query)
    
    def _parse_message(self, message: Dict, full: bool = False) -> Dict[str, Any]:
        """Parse Gmail message into structured data."""
        headers = message.get('payload', {}).get('headers', [])
        
        def get_header(name: str) -> str:
            for header in headers:
                if header['name'].lower() == name.lower():
                    return header.get('value', '')
            return ''
        
        result = {
            'id': message['id'],
            'thread_id': message.get('threadId'),
            'subject': get_header('Subject'),
            'sender': get_header('From'),
            'to': get_header('To'),
            'date': get_header('Date'),
            'labels': message.get('labelIds', []),
            'is_read': 'READ' in message.get('labelIds', []),
            'is_starred': 'STARRED' in message.get('labelIds', []),
        }
        
        if full:
            # Get body content
            body = self._get_message_body(message['payload'])
            result['body'] = body.get('text', '')
            result['html_body'] = body.get('html', '')
            
            # Get attachments info
            parts = message.get('payload', {}).get('parts', [])
            attachments = []
            for part in parts:
                if part.get('filename'):
                    attachments.append({
                        'filename': part['filename'],
                        'mime_type': part.get('mimeType'),
                        'size': part.get('body', {}).get('contentLength', 0)
                    })
            result['attachments'] = attachments
        
        return result
    
    def _get_message_body(self, payload: Dict) -> Dict[str, str]:
        """Extract text and HTML body from message payload."""
        result = {'text': '', 'html': ''}
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain':
                    data = part.get('body', {}).get('data', '')
                    if data:
                        result['text'] = base64.urlsafe_b64decode(data).decode('utf-8')
                elif part.get('mimeType') == 'text/html':
                    data = part.get('body', {}).get('data', '')
                    if data:
                        result['html'] = base64.urlsafe_b64decode(data).decode('utf-8')
                else:
                    # Recursively check nested parts
                    nested = self._get_message_body(part)
                    if nested['text']:
                        result['text'] = nested['text']
                    if nested['html']:
                        result['html'] = nested['html']
        else:
            # Single part message
            body_data = payload.get('body', {}).get('data', '')
            if body_data:
                decoded = base64.urlsafe_b64decode(body_data).decode('utf-8')
                if payload.get('mimeType') == 'text/html':
                    result['html'] = decoded
                else:
                    result['text'] = decoded
        
        return result
