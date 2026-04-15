# Email Service — Система умной email-рассылки

Веб-приложение для управляемой рассылки на 10 000+ контактов с ротацией доменов/ящиков, валидацией адресов, AI-вариативностью текста и real-time дашбордом.

## Стек

| Слой | Технология |
|------|-----------|
| Бэкенд | Python 3.12 / FastAPI |
| Фронтенд | React 18 / TypeScript / Tailwind CSS / Vite |
| БД | PostgreSQL 16 |
| Очередь | Celery + Redis 7 |
| AI-вариации | GPT-4 через OpenRouter |
| Real-time | WebSocket |
| Деплой | Docker Compose |

## Быстрый старт

### 1. Клонируйте и настройте окружение

```bash
cp .env.example .env
```

Отредактируйте `.env` — обязательно заполните:
- `FERNET_KEY` — генерация: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- `JWT_SECRET_KEY` — любая длинная случайная строка
- `OPENROUTER_API_KEY` — ключ OpenRouter (для генерации вариаций через GPT-4)

### 2. Запуск через Docker Compose

```bash
docker compose up --build
```

Это поднимет 6 сервисов:
- **postgres** — база данных (порт 5432)
- **redis** — брокер очередей (порт 6379)
- **backend** — FastAPI API (порт 8000)
- **celery-worker** — фоновые задачи (отправка, валидация, генерация)
- **celery-beat** — сброс счётчиков (часовых/дневных)
- **frontend** — React дашборд (порт 3000)

### 3. Миграции БД

```bash
docker compose exec backend alembic revision --autogenerate -m "init"
docker compose exec backend alembic upgrade head
```

### 4. Откройте дашборд

- Дашборд: **http://localhost:3000**
- API docs: **http://localhost:8000/docs**

Зарегистрируйте аккаунт и начните работу.

## Разработка (без Docker)

### Бэкенд

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

В отдельном терминале — Celery worker:

```bash
celery -A app.core.celery_app worker --loglevel=info
```

### Фронтенд

```bash
cd frontend
npm install
npm run dev
```

Дашборд будет доступен на **http://localhost:5173**, API проксируется на 8000.

## Структура проекта

```
email-service/
├── backend/
│   └── app/
│       ├── core/           — конфиг, БД, JWT, шифрование, Redis, Celery, WebSocket
│       ├── models/         — ORM-модели (User, Domain, Mailbox, Campaign, Contact, TextVariation, SendLog)
│       ├── schemas/        — Pydantic-схемы (API контракты)
│       ├── routers/        — HTTP/WS эндпоинты
│       ├── services/       — бизнес-логика (отправка, ротация, валидация, GPT-4)
│       ├── tasks/          — Celery-задачи
│       ├── utils/          — парсинг CSV, валидация email, хелперы
│       └── dependencies/   — FastAPI DI (auth guard, пагинация)
├── frontend/
│   └── src/
│       ├── api/            — Axios-клиент
│       ├── types/          — TypeScript интерфейсы
│       ├── hooks/          — WebSocket, прогресс кампании
│       ├── context/        — AuthContext
│       ├── pages/          — 7 страниц
│       ├── components/     — UI-компоненты
│       └── utils/          — форматирование, константы
├── docker-compose.yml
├── docker-compose.dev.yml
└── scripts/
```

## API эндпоинты

| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/api/auth/register` | Регистрация |
| POST | `/api/auth/login` | Вход (JWT) |
| GET | `/api/domains` | Список доменов с ящиками |
| POST | `/api/domains` | Добавить домен |
| POST | `/api/mailboxes/domain/{id}` | Добавить ящик |
| POST | `/api/mailboxes/{id}/test` | Тест SMTP-подключения |
| POST | `/api/campaigns` | Создать кампанию |
| POST | `/api/campaigns/{id}/start` | Запустить рассылку |
| POST | `/api/campaigns/{id}/pause` | Пауза |
| POST | `/api/campaigns/{id}/stop` | Остановить |
| POST | `/api/campaigns/{id}/contacts/upload` | Загрузить CSV/XLSX |
| POST | `/api/campaigns/{id}/contacts/validate` | Валидация адресов |
| POST | `/api/campaigns/{id}/variations/generate` | Генерация AI-вариаций |
| GET | `/api/campaigns/{id}/logs` | Лог отправок |
| WS | `/api/ws/campaigns/{id}` | Real-time прогресс |

## Переменные окружения

| Переменная | Описание | Обязательна |
|-----------|----------|-------------|
| `DATABASE_URL` | PostgreSQL (asyncpg) | да |
| `REDIS_URL` | Redis | да |
| `JWT_SECRET_KEY` | Секрет для JWT | да |
| `FERNET_KEY` | Ключ шифрования паролей ящиков | да |
| `OPENROUTER_API_KEY` | API-ключ OpenRouter (GPT-4) | для вариаций |
| `CORS_ORIGINS` | Разрешённые домены | нет |
