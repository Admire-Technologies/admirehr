# Admire HRMS

A comprehensive Human Resource Management System built with Next.js frontend and Django REST Framework backend.

## Project Structure

```
admire-hrms/
├── frontend/          # Next.js frontend application
├── backend/           # Django REST Framework backend
├── docker-compose.yml # Development environment setup
└── README.md         # Project documentation
```

## Quick Start

1. Clone the repository
2. Run `docker-compose up -d` to start PostgreSQL and Redis
3. Set up backend: `cd backend && pip install -r requirements.txt`
4. Set up frontend: `cd frontend && npm install`
5. Start development servers

## Technology Stack

**Frontend:**
- Next.js 14+ with TypeScript
- React 18+
- Tailwind CSS
- Metronic UI Theme

**Backend:**
- Django 4.2+ with Django REST Framework
- PostgreSQL database
- Redis for caching and WebSocket support
- Celery for background tasks

## Development Environment

The project uses Docker for development dependencies (PostgreSQL and Redis).