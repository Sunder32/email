# Changelog

## [unreleased]

- MVP-0001: Initial project architecture — backend (FastAPI, Celery, PostgreSQL, Redis), frontend (React, Tailwind CSS, Vite), Docker Compose setup
- MVP-0002: Backend models — User, Domain, Mailbox, Campaign, Contact, TextVariation, SendLog with SQLAlchemy ORM
- MVP-0003: Backend API — auth (JWT), domains/mailboxes CRUD, campaigns CRUD with start/pause/stop, contacts upload/validation, variations generation (GPT-4 via OpenRouter), send logs, WebSocket real-time updates
- MVP-0004: Backend services — SMTP sending, mailbox rotation with rate limiting, 3-level email validation, AI text variation generation, campaign orchestration engine
- MVP-0005: Backend Celery tasks — async campaign sending, contact validation, variation generation, hourly/daily counter reset
- MVP-0006: Frontend dashboard — login/register, domain/mailbox management, campaign creation wizard (compose, upload, validate, generate, launch), real-time monitoring with WebSocket, campaign history and detail views
- MVP-0007: Switched AI provider from Claude API to GPT-4 via OpenRouter
- MVP-0008: Production deployment setup — Nginx reverse proxy, SSL (Let's Encrypt), docker-compose.prod.yml, deploy.sh for Ubuntu
