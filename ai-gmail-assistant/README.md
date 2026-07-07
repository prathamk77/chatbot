# AI Gmail Assistant

A production-ready AI Gmail Assistant that automatically generates and sends professional emails using Gmail API and free AI models (Ollama).

## Features

- 📧 **Gmail Integration** - Read, send, reply, forward, search, label, and manage emails
- 🤖 **AI-Powered** - Generate professional emails using Ollama (Llama 3, Qwen, Gemma)
- 📅 **Scheduler** - Schedule emails with timezone support and recurring options
- 🔄 **Auto Follow-up** - Automatic follow-ups if no reply after 2, 5, or 7 days
- 📊 **Analytics** - Track sent emails, reply rates, response times, and more
- 🎨 **Modern UI** - Beautiful SaaS design with dark/light mode
- 🔐 **Secure** - OAuth 2.0, encrypted credentials, rate limiting, CSRF protection

## Tech Stack

### Frontend
- Next.js 15
- React 18
- TypeScript
- Tailwind CSS
- Shadcn UI
- Framer Motion

### Backend
- FastAPI (Python)
- Gmail API
- Google OAuth 2.0
- SQLite + SQLAlchemy

### AI
- Ollama (local LLM)
- No paid APIs

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.9+
- Docker & Docker Compose
- Ollama installed locally

### 1. Clone and Setup

```bash
cd ai-gmail-assistant
```

### 2. Environment Variables

```bash
# Copy example env files
cp .env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

Edit `backend/.env` with your Google OAuth credentials:
```
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/callback
OLLAMA_BASE_URL=http://host.docker.internal:11434
SECRET_KEY=your_secret_key
DATABASE_URL=sqlite:///./gmail_assistant.db
```

### 3. Install Dependencies

#### Backend
```bash
cd backend
pip install -r requirements.txt
```

#### Frontend
```bash
cd frontend
npm install
```

### 4. Start Ollama

```bash
# Pull a model
ollama pull llama3

# Run Ollama server (default port 11434)
ollama serve
```

### 5. Run with Docker Compose

```bash
docker-compose up --build
```

Or run separately:

#### Backend
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend
npm run dev
```

### 6. Access the Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Project Structure

```
ai-gmail-assistant/
├── backend/
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── models/       # Database models
│   │   ├── services/     # Business logic
│   │   └── utils/        # Utilities
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/          # Next.js pages
│   │   ├── components/   # React components
│   │   ├── lib/          # Utilities
│   │   ├── hooks/        # Custom hooks
│   │   ├── stores/       # State management
│   │   └── types/        # TypeScript types
│   ├── public/
│   ├── package.json
│   └── Dockerfile
├── docker/
│   └── nginx.conf
├── docker-compose.yml
├── README.md
└── .env.example
```

## Authentication

1. Click "Connect Gmail" on the dashboard
2. Sign in with your Google account
3. Grant necessary permissions
4. You'll be redirected back with access tokens

## Usage

### Compose Email

1. Navigate to "Compose"
2. Enter recipient email
3. Add subject (optional)
4. Write your prompt (e.g., "Send a proposal for website development")
5. Select tone (Professional, Friendly, Formal, etc.)
6. Click "Generate"
7. Review, edit, and send or schedule

### Auto Follow-up

Enable auto follow-up when composing:
- Set follow-up intervals (2, 5, 7 days)
- AI will generate and send follow-ups if no reply

### Templates

Use built-in templates for:
- Business Proposals
- Cold Outreach
- Follow-ups
- Invoices
- Meeting Requests
- And more...

## API Endpoints

### Authentication
- `POST /api/auth/login` - Google OAuth login
- `GET /api/auth/callback` - OAuth callback
- `POST /api/auth/logout` - Logout

### Emails
- `GET /api/emails` - List emails
- `GET /api/emails/{id}` - Get email details
- `POST /api/emails/send` - Send email
- `POST /api/emails/draft` - Save draft
- `DELETE /api/emails/{id}` - Delete email

### AI
- `POST /api/ai/generate` - Generate email content
- `POST /api/ai/summarize` - Summarize email
- `POST /api/ai/improve` - Improve grammar
- `POST /api/ai/translate` - Translate email

### Scheduler
- `GET /api/schedule` - List scheduled emails
- `POST /api/schedule` - Schedule email
- `DELETE /api/schedule/{id}` - Cancel schedule

## Security

- OAuth 2.0 authentication
- Encrypted token storage
- Rate limiting on API endpoints
- CSRF protection
- Input validation
- Secure session management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

MIT License

## Support

For issues and questions, please open an issue on GitHub.
