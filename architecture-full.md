# Система массовой email-рассылки — Полная архитектура

## Общее описание

Веб-приложение для управляемой рассылки на 10 000+ контактов с ротацией доменов и почтовых ящиков, валидацией адресов, вариативностью текста и real-time дашбордом.

---

## Стек технологий

| Компонент | Технология |
|-----------|-----------|
| Фронтенд (дашборд) | React + Tailwind CSS |
| Бэкенд API | Python / FastAPI |
| База данных | PostgreSQL |
| Очередь задач | Celery + Redis |
| SMTP-отправка | smtplib (Python) |
| Валидация email | py3dns + SMTP-проверка |
| Генерация вариаций | GPT-4 через OpenRouter (openai/gpt-4) |
| Real-time обновления | WebSocket (FastAPI WebSocket / Socket.IO) |
| Деплой | VPS (Ubuntu) + Docker Compose |

---

## Структура базы данных

### Таблица `domains`

- `id` — PK
- `name` — имя домена (например, company.ru)
- `hourly_limit` — лимит писем в час
- `daily_limit` — лимит писем в день
- `sent_this_hour` — счётчик отправленных за текущий час
- `sent_today` — счётчик отправленных за сегодня
- `is_active` — включен/выключен
- `created_at`

### Таблица `mailboxes`

- `id` — PK
- `domain_id` — FK → domains
- `email` — адрес ящика
- `smtp_host` — SMTP-сервер
- `smtp_port` — порт (465/587)
- `login` — логин
- `password` — пароль (зашифрован)
- `use_tls` — bool
- `hourly_limit` — лимит писем в час для этого ящика
- `daily_limit` — лимит писем в день
- `sent_this_hour` — счётчик
- `sent_today` — счётчик
- `is_active` — включен/выключен

### Таблица `contacts`

- `id` — PK
- `email` — адрес получателя
- `is_valid` — результат валидации (null / true / false)
- `validation_error` — причина невалидности
- `campaign_id` — FK → campaigns

### Таблица `campaigns`

- `id` — PK
- `name` — название рассылки
- `original_subject` — исходная тема
- `original_body` — исходный текст письма
- `total_contacts` — всего контактов
- `sent_count` — отправлено
- `failed_count` — ошибки
- `status` — draft / validating / ready / running / paused / completed
- `rotate_every_n` — менять связку каждые N писем (по умолчанию 5)
- `delay_min_sec` — минимальная задержка между письмами
- `delay_max_sec` — максимальная задержка
- `started_at`
- `completed_at`

### Таблица `send_log`

- `id` — PK
- `campaign_id` — FK → campaigns
- `contact_id` — FK → contacts
- `mailbox_id` — FK → mailboxes
- `subject_used` — тема, которая была отправлена
- `body_preview` — первые 200 символов тела письма
- `status` — sent / failed / skipped
- `error_message` — если failed
- `sent_at` — таймстемп

### Таблица `text_variations`

- `id` — PK
- `campaign_id` — FK → campaigns
- `subject_variant` — вариация темы
- `iceberg_variant` — вариация первого абзаца
- `times_used` — сколько раз использована

---

## Модули системы

### 1. Модуль управления доменами и ящиками

**API-эндпоинты:**

- `POST /api/domains` — добавить домен
- `GET /api/domains` — список доменов с ящиками
- `POST /api/domains/{id}/mailboxes` — добавить ящик к домену
- `DELETE /api/mailboxes/{id}` — удалить ящик
- `POST /api/mailboxes/{id}/test` — тестовая отправка (проверить что SMTP работает)

**Логика ротации:**

```
pool = все активные связки (domain + mailbox), у которых не исчерпан лимит
current_index = 0

для каждого письма:
    связка = pool[current_index]
    отправить письмо через связку
    обновить счётчики связки
    
    если отправлено N писем через эту связку:
        current_index = (current_index + 1) % len(pool)
    
    если у текущей связки исчерпан лимит:
        убрать из pool
        current_index = current_index % len(pool)
    
    если pool пуст:
        поставить кампанию на паузу, уведомить
```

### 2. Модуль валидации email

**Три уровня проверки:**

1. **Синтаксис** — регулярное выражение, проверка формата.
2. **MX-запись** — DNS-запрос, существует ли почтовый домен. Используем `dns.resolver` из `dnspython`.
3. **SMTP-проверка** — подключаемся к MX-серверу получателя, делаем `EHLO` → `MAIL FROM` → `RCPT TO` и смотрим ответ. Не отправляем само письмо. Работает не везде (catch-all домены, greylisting).

**Процесс:**

```
загрузили базу контактов
    → запускаем валидацию (отдельная Celery-задача)
    → каждый контакт проходит 3 уровня
    → результат записывается в contacts.is_valid
    → на дашборде видно прогресс валидации
    → после завершения: "Из 10 000 валидных 9 347, невалидных 653"
    → можно запускать рассылку только по валидным
```

### 3. Модуль генерации вариаций текста

**Принцип:** перед запуском кампании генерируем пул вариаций (20–50 штук) через GPT-4 (OpenRouter).

**Промпт для генерации:**

```
Перефразируй тему письма и первый абзац.
Сохрани смысл, тон и длину. Измени формулировки, порядок слов,
синонимы. Не добавляй ничего нового.

Оригинальная тема: {subject}
Оригинальный первый абзац: {iceberg}

Верни JSON: {"subject": "...", "iceberg": "..."}
```

**При отправке:**

- Каждое чётное письмо использует оригинал.
- Каждое нечётное — случайную вариацию из пула.
- Вариации ротируются равномерно (round-robin или random без повторов подряд).

### 4. Модуль очереди отправки (Celery worker)

**Задача `send_campaign`:**

```python
@celery.task
def send_campaign(campaign_id):
    campaign = get_campaign(campaign_id)
    contacts = get_valid_contacts(campaign_id, status='pending')
    pool = get_active_mailbox_pool()
    variations = get_variations(campaign_id)
    
    mailbox_index = 0
    sent_via_current = 0
    
    for contact in contacts:
        if campaign.status == 'paused':
            break
        
        # Выбрать связку
        mailbox = pool[mailbox_index]
        
        # Выбрать текст
        if contact.sequence_number % 2 == 0:
            subject, body = campaign.original_subject, campaign.original_body
        else:
            variation = pick_next_variation(variations)
            subject = variation.subject_variant
            body = replace_iceberg(campaign.original_body, variation.iceberg_variant)
        
        # Отправить
        try:
            smtp_send(mailbox, contact.email, subject, body)
            log_send(campaign_id, contact.id, mailbox.id, 'sent', subject, body)
            campaign.sent_count += 1
        except Exception as e:
            log_send(campaign_id, contact.id, mailbox.id, 'failed', error=str(e))
            campaign.failed_count += 1
        
        # Ротация
        sent_via_current += 1
        if sent_via_current >= campaign.rotate_every_n:
            mailbox_index = (mailbox_index + 1) % len(pool)
            sent_via_current = 0
        
        # Обновить счётчики и лимиты
        update_counters(mailbox)
        refresh_pool_if_needed(pool)
        
        # Задержка
        delay = random.uniform(campaign.delay_min_sec, campaign.delay_max_sec)
        time.sleep(delay)
        
        # Уведомить дашборд через WebSocket
        broadcast_progress(campaign)
```

### 5. Модуль дашборда (фронтенд)

**Экраны:**

1. **Настройки доменов/ящиков** — таблица доменов, к каждому раскрываются ящики. Кнопка "Тест" для проверки SMTP.

2. **Создание кампании:**
   - Поле для темы письма
   - Редактор тела письма (отметка где "айсберг")
   - Загрузка CSV с контактами
   - Настройки: частота ротации, задержки, лимиты
   - Кнопка "Сгенерировать вариации" → показ превью
   - Кнопка "Запустить валидацию"
   - Кнопка "Запустить рассылку"

3. **Мониторинг кампании (real-time):**
   - Прогресс-бар: отправлено / осталось / ошибки
   - Таймер: прошло времени / ETA
   - Текущая связка: домен + ящик
   - Лог последних 20 отправок (кому, с какого ящика, какая вариация)
   - График скорости отправки (писем/минуту)

4. **История:**
   - Все кампании, статистика по каждой
   - Детальный лог: фильтр по домену, ящику, статусу

---

## Безопасность

- Пароли ящиков шифруются в базе (Fernet / AES-256).
- Доступ к дашборду — по логину/паролю (JWT-токены).
- SMTP-соединения — только TLS/SSL.
- Rate limiting на API.
- Логи не содержат паролей.

---

## Деплой

```
docker-compose.yml:
  - app (FastAPI + React build)
  - postgres
  - redis
  - celery-worker
  - celery-beat (сброс часовых/дневных счётчиков)
```

Минимальные требования к серверу: VPS с 2 CPU, 4 GB RAM, 20 GB SSD. Этого хватит на рассылку 10 000 писем.

---

## Примерный таймлайн разработки

| Этап | Время |
|------|-------|
| БД + API доменов/ящиков | 2–3 дня |
| Валидация email | 1–2 дня |
| Генерация вариаций (GPT-4) | 1 день |
| Очередь отправки + ротация | 3–4 дня |
| Дашборд (фронтенд) | 3–4 дня |
| Тестирование + отладка | 2–3 дня |
| **Итого** | **~2–3 недели** |
