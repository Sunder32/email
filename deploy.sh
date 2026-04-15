#!/bin/bash
# ============================================================
# Email Service — Deploy script for Ubuntu
# Domain: email-service.tmsasub.ru (212.67.8.111)
# ============================================================
set -e

DOMAIN="email-service.tmsasub.ru"
PROJECT_DIR="/opt/email-service"
REPO="https://github.com/Sunder32/email.git"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Email Service — Server Setup ===${NC}"

# -------------------------------------------------------
# 1. System update + dependencies
# -------------------------------------------------------
echo -e "${GREEN}[1/8] Updating system...${NC}"
apt-get update
apt-get install -y curl git ufw

# -------------------------------------------------------
# 2. Install Docker
# -------------------------------------------------------
echo -e "${GREEN}[2/8] Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
else
    echo "Docker already installed."
fi

if ! docker compose version &> /dev/null; then
    apt-get install -y docker-compose-plugin
fi

# -------------------------------------------------------
# 3. Firewall
# -------------------------------------------------------
echo -e "${GREEN}[3/8] Configuring firewall...${NC}"
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# -------------------------------------------------------
# 4. Clone project
# -------------------------------------------------------
echo -e "${GREEN}[4/8] Cloning project...${NC}"
if [ -d "$PROJECT_DIR" ]; then
    cd "$PROJECT_DIR"
    git pull origin main
else
    git clone "$REPO" "$PROJECT_DIR"
    cd "$PROJECT_DIR"
fi

# -------------------------------------------------------
# 5. Create .env
# -------------------------------------------------------
echo -e "${GREEN}[5/8] Configuring environment...${NC}"
if [ ! -f .env ]; then
    cp .env.example .env

    JWT_SECRET=$(openssl rand -hex 32)
    DB_PASS=$(openssl rand -hex 16)

    sed -i "s|^JWT_SECRET_KEY=.*|JWT_SECRET_KEY=$JWT_SECRET|" .env
    sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$DB_PASS|" .env
    sed -i "s|^POSTGRES_USER=.*|POSTGRES_USER=emailadmin|" .env
    sed -i "s|postgres:postgres|emailadmin:$DB_PASS|g" .env
    sed -i "s|^CORS_ORIGINS=.*|CORS_ORIGINS=[\"https://$DOMAIN\",\"http://$DOMAIN\"]|" .env

    echo -e "${YELLOW}>>> .env created. Fill in FERNET_KEY and OPENROUTER_API_KEY:${NC}"
    echo -e "${YELLOW}    nano $PROJECT_DIR/.env${NC}"
    echo ""
    echo -e "${YELLOW}Generate FERNET_KEY after build:${NC}"
    echo -e "    docker run --rm python:3.12-slim pip install cryptography -q && python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
fi

# -------------------------------------------------------
# 6. Create dirs for certbot
# -------------------------------------------------------
mkdir -p certbot/www certbot/conf

# -------------------------------------------------------
# 7. Build and start (HTTP first)
# -------------------------------------------------------
echo -e "${GREEN}[6/8] Building and starting services (HTTP mode)...${NC}"
docker compose -f docker-compose.prod.yml up --build -d

echo -e "${GREEN}Waiting for services to start...${NC}"
sleep 15

# -------------------------------------------------------
# 8. Database migrations
# -------------------------------------------------------
echo -e "${GREEN}[7/8] Running database migrations...${NC}"
docker compose -f docker-compose.prod.yml exec -T backend alembic revision --autogenerate -m "init" 2>/dev/null || true
docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head

# -------------------------------------------------------
# 9. SSL certificate
# -------------------------------------------------------
echo -e "${GREEN}[8/8] Obtaining SSL certificate...${NC}"
docker compose -f docker-compose.prod.yml run --rm certbot certonly \
    --webroot -w /var/www/certbot \
    -d "$DOMAIN" \
    --email admin@tmsasub.ru \
    --agree-tos --no-eff-email

# Switch to HTTPS config
cp nginx/conf.d/app.conf nginx/conf.d/default.conf
docker compose -f docker-compose.prod.yml restart nginx

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Email Service deployed with SSL!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "  App:  ${GREEN}https://$DOMAIN${NC}"
echo -e "  API:  ${GREEN}https://$DOMAIN/api/docs${NC}"
echo ""
echo -e "${YELLOW}Commands:${NC}"
echo -e "  cd $PROJECT_DIR"
echo -e "  docker compose -f docker-compose.prod.yml logs -f          # logs"
echo -e "  docker compose -f docker-compose.prod.yml restart          # restart"
echo -e "  docker compose -f docker-compose.prod.yml down             # stop"
echo ""
echo -e "${YELLOW}SSL auto-renew (add to crontab):${NC}"
echo -e "  0 3 * * 1 cd $PROJECT_DIR && docker compose -f docker-compose.prod.yml run --rm certbot renew && docker compose -f docker-compose.prod.yml restart nginx"
echo ""
