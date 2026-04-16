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
- MVP-0009: Soft email validation — SMTP RCPT TO timeouts/4xx/blocked ports no longer mark addresses as invalid (only explicit 5xx rejection does). Prevents false-positives when VPS has port 25 blocked or no PTR record.
- MVP-0010: Skip-validation flag on campaigns — option to send without validation when the user trusts the list.
- MVP-0011: Send-log detail upgrade — logs now show recipient email, sender mailbox, and a human-readable error label ("Неверный пароль", "Адрес не существует", "Таймаут SMTP" etc.) instead of raw contact IDs.
- MVP-0012: Campaign detail page — new "Contacts" tab with filters (validation status, send status, email search) and a "Report" block with validation breakdown.
- MVP-0013: CSV export for campaign report (email, validation, send status, error, mailbox, subject, timestamp).
- MVP-0014: "Mark all valid" action to override validation results for campaigns where SMTP check is unreliable.
- MVP-0015: Retry on transient SMTP errors (4xx, timeout, connection reset) with exponential backoff; permanent (5xx) failures fail immediately.
- MVP-0016: Progress bar now shows sent/total (not sent/valid), and dashboard includes invalid-count statistic.
- MVP-0017: Fix blocking `time.sleep()` in async `send_campaign` — now uses `await asyncio.sleep` and `asyncio.to_thread` for SMTP so the event loop is never blocked.
- MVP-0018: Real-time dashboard now actually works — Celery worker publishes events to Redis, FastAPI subscribes on startup and forwards them to WebSocket clients (previous code had `ws_broadcast=None` all the time).
- MVP-0019: Celery tasks now `await engine.dispose()` in `finally`, fixing DB-pool leak after many runs.
- MVP-0020: Mailbox/domain counters are now incremented via atomic SQL (`sent_this_hour = sent_this_hour + 1`) — race-safe under concurrent workers.
- MVP-0021: WebSocket reconnect timer cleaned up on unmount — fixes connection leak on navigation.
- MVP-0022: Upload size limit (10 MB configurable), empty-file detection, specific error types for bad CSV/XLSX.
- MVP-0023: JWT_SECRET_KEY and FERNET_KEY are now mandatory — app refuses to start with defaults.
- MVP-0024: CORS allow_methods/allow_headers restricted from wildcard to actual needs.
- MVP-0025: Campaign `start_campaign` preserves `valid_contacts` from prior validation instead of overwriting with `total_contacts`.
- MVP-0026: `validation_service` no longer sets `valid_contacts` twice — uses a single `COUNT` query.
- MVP-0027: Falsy-zero bug fixed on monitor page (`??` instead of `||`); NaN campaign ID guarded.
- MVP-0028: `onError` handlers on all frontend mutations (pause/stop/validate/generate/upload) via shared `handleError` helper.
- MVP-0029: Body-scroll lock on open Modal; `key` in log feed uses unique composite instead of array index.
- MVP-0030: Hardcoded values extracted to config — SMTP timeouts, retry backoff, polling intervals, upload size limit.
- MVP-0031: Dead code removed — unused `random` import, `User` import in domains router, `index` param in `pick_variation`, `pass` branch.
