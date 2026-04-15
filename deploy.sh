#!/bin/bash
# ============================================================
# Email Service — Deploy script for Ubuntu (212.67.8.111)
# ============================================================
# Usage: ssh root@212.67.8.111 'bash -s' < deploy.sh
# Or: copy to server and run: chmod +x deploy.sh && ./deploy.sh
# ============================================================
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Email Service — Server Setup ===${NC}"

# -------------------------------------------------------
# 1. System update + dependencies
# -------------------------------------------------------
echo -e "${GREEN}[1/7] Updating system...${NC}"
apt-get update && apt-get upgrade -y
apt-get install -y curl git ufw

# -------------------------------------------------------
# 2. Install Docker
# -------------------------------------------------------
echo -e "${GREEN}[2/7] Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
else
    echo "Docker already installed."
fi

# Install Docker Compose plugin
if ! docker compose version &> /dev/null; then
    apt-get install -y docker-compose-plugin
fi

# -------------------------------------------------------
# 3. Firewall
# -------------------------------------------------------
echo -e "${GREEN}[3/7] Configuring firewall...${NC}"
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# -------------------------------------------------------
# 4. Clone project
# -------------------------------------------------------
echo -e "${GREEN}[4/7] Cloning project...${NC}"
PROJECT_DIR="/opt/email-service"

if [ -d "$PROJECT_DIR" ]; then
    cd "$PROJECT_DIR"
    git pull origin main
else
    git clone https://github.com/Sunder32/email.git "$PROJECT_DIR"
    cd "$PROJECT_DIR"
fi

# -------------------------------------------------------
# 5. Create .env if not exists
# -------------------------------------------------------
echo -e "${GREEN}[5/7] Configuring environment...${NC}"
if [ ! -f .env ]; then
    cp .env.example .env

    # Generate keys
    FERNET=$(docker run --rm python:3.12-slim python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || echo "GENERATE_ME")
    JWT_SECRET=$(openssl rand -hex 32)
    DB_PASS=$(openssl rand -hex 16)

    sed -i "s|^FERNET_KEY=.*|FERNET_KEY=$FERNET|" .env
    sed -i "s|^JWT_SECRET_KEY=.*|JWT_SECRET_KEY=$JWT_SECRET|" .env
    sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$DB_PASS|" .env
    sed -i "s|^POSTGRES_USER=.*|POSTGRES_USER=emailadmin|" .env
    sed -i "s|emailadmin:AAZRg6sizvF3P8scyw3lZw|emailadmin:$DB_PASS|g" .env
    sed -i "s|^CORS_ORIGINS=.*|CORS_ORIGINS=[\"http://212.67.8.111\",\"https://212.67.8.111\"]|" .env

    echo -e "${YELLOW}>>> .env created. Edit it to add OPENROUTER_API_KEY:${NC}"
    echo -e "${YELLOW}    nano $PROJECT_DIR/.env${NC}"
fi

# -------------------------------------------------------
# 6. Create certbot dirs
# -------------------------------------------------------
mkdir -p certbot/www certbot/conf

# -------------------------------------------------------
# 7. Build and start (HTTP first)
# -------------------------------------------------------
echo -e "${GREEN}[6/7] Building and starting services...${NC}"
docker compose -f docker-compose.prod.yml up --build -d

echo -e "${GREEN}Waiting for services to start...${NC}"
sleep 10

# -------------------------------------------------------
# 8. Database migrations
# -------------------------------------------------------
echo -e "${GREEN}[7/7] Running database migrations...${NC}"
docker compose -f docker-compose.prod.yml exec -T backend alembic revision --autogenerate -m "init" 2>/dev/null || true
docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Email Service deployed!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "  App: ${GREEN}http://212.67.8.111${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Edit .env if needed:  nano $PROJECT_DIR/.env"
echo -e "  2. Get SSL certificate:  Run the commands below"
echo ""
echo -e "${YELLOW}=== SSL Setup (Let's Encrypt) ===${NC}"
echo ""
echo "  Since you're using an IP address (not a domain),"
echo "  Let's Encrypt won't issue a certificate for bare IPs."
echo ""
echo "  Option A: If you have a domain pointing to 212.67.8.111:"
echo "    1. Update nginx/conf.d/app.conf — replace 212.67.8.111 with your domain"
echo "    2. Run:"
echo "       cd $PROJECT_DIR"
echo "       docker compose -f docker-compose.prod.yml run --rm certbot certonly \\"
echo "         --webroot -w /var/www/certbot \\"
echo "         -d YOUR_DOMAIN.com --email YOUR_EMAIL --agree-tos --no-eff-email"
echo "    3. Switch to SSL config:"
echo "       cp nginx/conf.d/app.conf nginx/conf.d/default.conf"
echo "       docker compose -f docker-compose.prod.yml restart nginx"
echo ""
echo "  Option B: Use HTTP only (current setup works on http://212.67.8.111)"
echo ""
