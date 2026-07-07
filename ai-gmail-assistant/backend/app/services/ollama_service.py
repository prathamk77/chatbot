"""Ollama AI service for email generation and analysis."""

import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.utils.config import settings


class OllamaService:
    """Service for interacting with Ollama API for AI-powered features."""
    
    # Email tones
    TONES = [
        "Professional", "Friendly", "Formal", "Confident",
        "Persuasive", "Luxury", "Minimal", "Corporate", "Casual"
    ]
    
    # Email categories
    CATEGORIES = [
        "Cold Outreach", "Follow-up", "Proposal", "Quotation",
        "Invoice", "Appointment", "Meeting", "Reminder",
        "Thank You", "Support", "Job Application", "Marketing",
        "Sales", "Business Introduction"
    ]
    
    def __init__(self):
        """Initialize Ollama service."""
        self.base_url = settings.ollama_base_url.rstrip('/')
        self.model = settings.ollama_model
    
    async def generate_email(self, prompt: str, recipient: str,
                            subject_hint: str = None, tone: str = "Professional",
                            context: str = None) -> Dict[str, str]:
        """Generate a complete email based on prompt."""
        
        system_prompt = f"""You are a professional email assistant. Generate a professional email based on the user's request.

Tone: {tone}
Recipient: {recipient}
{f'Context: {context}' if context else ''}

Generate the email with:
1. A compelling subject line
2. Appropriate greeting
3. Clear and concise body
4. Strong call-to-action
5. Professional signature

Format your response as JSON:
{{
    "subject": "Generated subject line",
    "greeting": "Dear ...",
    "body": "Email body content",
    "closing": "Best regards,",
    "signature": "Your Name"
}}
"""
        
        user_prompt = f"Write an email: {prompt}"
        if subject_hint:
            user_prompt += f"\nSubject hint: {subject_hint}"
        
        response = await self._generate_completion(system_prompt, user_prompt)
        
        return response
    
    async def suggest_reply(self, email_content: str, tone: str = "Professional") -> str:
        """Suggest a reply to an email."""
        
        system_prompt = f"""You are a professional email assistant. Suggest a concise and appropriate reply to the following email.

Tone: {tone}

Provide only the reply content without any explanations."""
        
        user_prompt = f"Reply to this email:\n\n{email_content}"
        
        response = await self._generate_completion(system_prompt, user_prompt)
        return response
    
    async def summarize_email(self, email_content: str) -> str:
        """Summarize a long email into key points."""
        
        system_prompt = """Summarize the following email into 3-5 bullet points highlighting the most important information.

Format as bullet points only."""
        
        user_prompt = f"Summarize this email:\n\n{email_content}"
        
        response = await self._generate_completion(system_prompt, user_prompt)
        return response
    
    async def extract_action_items(self, email_content: str) -> List[str]:
        """Extract action items from an email."""
        
        system_prompt = """Extract all action items and tasks from the following email.

Return as a JSON array of strings: ["action item 1", "action item 2", ...]"""
        
        user_prompt = f"Extract action items from:\n\n{email_content}"
        
        response = await self._generate_completion(system_prompt, user_prompt)
        
        # Parse JSON response
        try:
            import json
            items = json.loads(response.strip())
            return items if isinstance(items, list) else [response]
        except:
            return [response]
    
    async def detect_sentiment(self, email_content: str) -> str:
        """Detect sentiment of an email (positive, negative, neutral)."""
        
        system_prompt = """Analyze the sentiment of the following email.
Respond with only one word: positive, negative, or neutral."""
        
        user_prompt = f"Analyze sentiment:\n\n{email_content}"
        
        response = await self._generate_completion(system_prompt, user_prompt)
        sentiment = response.strip().lower()
        
        if sentiment in ['positive', 'negative', 'neutral']:
            return sentiment
        return 'neutral'
    
    async def improve_grammar(self, text: str) -> str:
        """Improve grammar and clarity of text."""
        
        system_prompt = """Improve the grammar, clarity, and professionalism of the following text.
Keep the original meaning intact. Return only the improved text."""
        
        user_prompt = f"Improve this text:\n\n{text}"
        
        response = await self._generate_completion(system_prompt, user_prompt)
        return response
    
    async def rewrite_email(self, text: str, tone: str = "Professional") -> str:
        """Rewrite email content with a different tone."""
        
        system_prompt = f"""Rewrite the following email content with a {tone} tone.
Maintain the core message but adjust the language and style."""
        
        user_prompt = f"Rewrite this:\n\n{text}"
        
        response = await self._generate_completion(system_prompt, user_prompt)
        return response
    
    async def generate_subject_lines(self, email_body: str, count: int = 5) -> List[str]:
        """Generate multiple subject line options."""
        
        system_prompt = f"""Generate {count} compelling subject lines for the following email.
Each subject line should be concise (under 60 characters) and attention-grabbing.

Return as a JSON array of strings."""
        
        user_prompt = f"Generate subject lines for:\n\n{email_body}"
        
        response = await self._generate_completion(system_prompt, user_prompt)
        
        try:
            import json
            subjects = json.loads(response.strip())
            return subjects if isinstance(subjects, list) else [response]
        except:
            return [response]
    
    async def translate_email(self, text: str, target_language: str) -> str:
        """Translate email content to another language."""
        
        system_prompt = f"""Translate the following text to {target_language}.
Maintain the professional tone and formatting."""
        
        user_prompt = f"Translate:\n\n{text}"
        
        response = await self._generate_completion(system_prompt, user_prompt)
        return response
    
    async def categorize_email(self, email_content: str) -> str:
        """Categorize email into predefined categories."""
        
        categories_str = ", ".join(self.CATEGORIES)
        
        system_prompt = f"""Categorize the following email into one of these categories:
{categories_str}

Respond with only the category name."""
        
        user_prompt = f"Categorize:\n\n{email_content}"
        
        response = await self._generate_completion(system_prompt, user_prompt)
        category = response.strip()
        
        # Validate category
        if category in self.CATEGORIES:
            return category
        
        # Find closest match
        for cat in self.CATEGORIES:
            if cat.lower() in category.lower():
                return cat
        
        return 'General'
    
    async def detect_spam(self, email_content: str) -> bool:
        """Detect if an email is likely spam."""
        
        system_prompt = """Analyze if the following email is spam or legitimate.
Consider common spam indicators like urgency, suspicious links, requests for personal info, etc.

Respond with only: spam or legitimate."""
        
        user_prompt = f"Analyze:\n\n{email_content}"
        
        response = await self._generate_completion(system_prompt, user_prompt)
        result = response.strip().lower()
        
        return 'spam' in result
    
    async def generate_follow_up(self, previous_email: str, days_since: int) -> str:
        """Generate a follow-up email based on previous communication."""
        
        system_prompt = f"""Generate a polite follow-up email. The original email was sent {days_since} days ago.

The follow-up should:
1. Be friendly and not pushy
2. Reference the previous email
3. Ask for a response or update
4. Maintain professionalism

Generate a complete email with subject and body."""
        
        user_prompt = f"Previous email:\n\n{previous_email}\n\nGenerate a follow-up."
        
        response = await self._generate_completion(system_prompt, user_prompt)
        return response
    
    async def _generate_completion(self, system_prompt: str, user_prompt: str) -> str:
        """Make completion request to Ollama API."""
        
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": user_prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 1024
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                return result.get('response', '')
        except httpx.TimeoutException:
            raise Exception("Ollama API timeout. Make sure Ollama is running.")
        except httpx.ConnectionError:
            raise Exception(f"Cannot connect to Ollama at {self.base_url}. Is Ollama running?")
        except Exception as e:
            raise Exception(f"Ollama API error: {str(e)}")
    
    async def check_connection(self) -> bool:
        """Check if Ollama service is available."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except:
            return False
    
    async def list_models(self) -> List[str]:
        """List available Ollama models."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                result = response.json()
                return [model['name'] for model in result.get('models', [])]
        except:
            return []


# Singleton instance
ollama_service = OllamaService()
