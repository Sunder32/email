#!/bin/bash
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== Email Service — Запуск ===${NC}"
echo ""

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker не установлен. Установите Docker: https://docs.docker.com/get-docker/${NC}"
    exit 1
fi

if ! docker info &> /dev/null 2>&1; then
    echo -e "${RED}Docker не запущен. Запустите Docker Desktop.${NC}"
    exit 1
fi

# Создание .env если нет
if [ ! -f .env ]; then
    echo -e "${YELLOW}Файл .env не найден. Создаю из .env.example...${NC}"
    cp .env.example .env

    # Генерация FERNET_KEY
    if command -v python3 &> /dev/null; then
        FERNET=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || true)
    elif command -v python &> /dev/null; then
        FERNET=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || true)
    fi

    if [ -n "$FERNET" ]; then
        sed -i "s|^FERNET_KEY=.*|FERNET_KEY=$FERNET|" .env
        echo -e "${GREEN}FERNET_KEY сгенерирован автоматически.${NC}"
    else
        echo -e "${YELLOW}Не удалось сгенерировать FERNET_KEY. Заполните вручную в .env${NC}"
    fi

    # Генерация JWT_SECRET_KEY
    JWT_SECRET=$(openssl rand -hex 32 2>/dev/null || head -c 64 /dev/urandom | base64 | tr -d '\n' 2>/dev/null || echo "change-me-$(date +%s)")
    sed -i "s|^JWT_SECRET_KEY=.*|JWT_SECRET_KEY=$JWT_SECRET|" .env
    echo -e "${GREEN}JWT_SECRET_KEY сгенерирован автоматически.${NC}"

    echo ""
    echo -e "${YELLOW}Проверьте .env и заполните OPENROUTER_API_KEY для генерации вариаций.${NC}"
    echo ""
fi

# Сборка и запуск
echo -e "${GREEN}Собираю и запускаю контейнеры...${NC}"
docker compose up --build -d

echo ""
echo -e "${GREEN}Ожидаю готовности PostgreSQL...${NC}"
sleep 5

# Миграции
echo -e "${GREEN}Запускаю миграции базы данных...${NC}"
docker compose exec -T backend alembic revision --autogenerate -m "init" 2>/dev/null || true
docker compose exec -T backend alembic upgrade head

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  Email Service запущен!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "  Дашборд:   ${GREEN}http://localhost:3000${NC}"
echo -e "  API:       ${GREEN}http://localhost:8000${NC}"
echo -e "  API Docs:  ${GREEN}http://localhost:8000/docs${NC}"
echo ""
echo -e "  Зарегистрируйте аккаунт и начните работу."
echo ""
echo -e "${YELLOW}Команды:${NC}"
echo -e "  docker compose logs -f          — логи всех сервисов"
echo -e "  docker compose logs -f backend  — логи бэкенда"
echo -e "  docker compose down             — остановить"
echo ""
