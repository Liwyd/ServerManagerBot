#!/bin/bash
set -e

# ServerManagerBot - One-line Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/Liwyd/ServerManagerBot/master/install.sh | sudo bash

INSTALL_DIR="/opt/servermanagerbot"
REPO_URL="https://github.com/Liwyd/ServerManagerBot.git"
BRANCH="master"
DOCKER_IMAGE="liwyd/servermanagerbot:latest"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()    { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()   { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()  { echo -e "${RED}[ERROR]${NC} $*"; }
header() { echo -e "\n${CYAN}=== $* ===${NC}\n"; }

command_exists() { command -v "$1" >/dev/null 2>&1; }

generate_password() {
    if command_exists openssl; then
        openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 32
    elif command_exists python3; then
        python3 -c "import secrets; print(secrets.token_urlsafe(32))"
    else
        head -c 32 /dev/urandom | base64 | tr -dc 'a-zA-Z0-9' | head -c 32
    fi
}

header "ServerManagerBot Installer"

if [ "$EUID" -ne 0 ]; then
    error "This installer must be run as root (use sudo)."
    exit 1
fi

OS="$(uname -s)"
ARCH="$(uname -m)"
log "Detected OS: $OS, Architecture: $ARCH"

if ! command_exists docker; then
    log "Installing Docker..."
    if [ "$OS" = "Linux" ]; then
        curl -fsSL https://get.docker.com | sh
    else
        error "Please install Docker manually for $OS."
        exit 1
    fi
    log "Docker installed."
else
    log "Docker already installed: $(docker --version)"
fi

if ! docker compose version >/dev/null 2>&1; then
    error "Docker Compose plugin not found. Please install Docker Compose v2."
    exit 1
fi
log "Docker Compose available: $(docker compose version --short)"

EXISTING_ENV=false
if [ -d "$INSTALL_DIR" ]; then
    warn "Existing installation detected at $INSTALL_DIR"
    if [ -f "$INSTALL_DIR/.env" ]; then
        warn "Existing .env file found. Preserving it."
        EXISTING_ENV=true
    fi
    cd "$INSTALL_DIR"
    docker compose down 2>/dev/null || true
    log "Updating source code..."
    git pull origin "$BRANCH" 2>/dev/null || {
        warn "Git pull failed. Re-cloning..."
        cd /
        rm -rf "$INSTALL_DIR"
        git clone --branch "$BRANCH" "$REPO_URL" "$INSTALL_DIR"
        cd "$INSTALL_DIR"
    }
else
    log "Cloning repository..."
    git clone --branch "$BRANCH" "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

if [ ! -f "$INSTALL_DIR/.env" ] || [ "$EXISTING_ENV" != "true" ]; then
    log "Creating .env file..."
    DB_PASSWORD=$(generate_password)
    PG_PASSWORD=$(generate_password)

    echo -n "Enter your Telegram Bot Token: "
    read -r BOT_TOKEN
    if [ -z "$BOT_TOKEN" ]; then
        error "Telegram Bot Token is required."
        exit 1
    fi

    echo -n "Enter your Telegram Admin ID: "
    read -r ADMIN_ID
    if [ -z "$ADMIN_ID" ]; then
        error "Telegram Admin ID is required."
        exit 1
    fi

    cat > "$INSTALL_DIR/.env" << EOF
DATABASE_USERNAME=smbuser
DATABASE_PASSWORD=${DB_PASSWORD}
DATABASE_NAME=servermanagerbot
DATABASE_HOST=localhost
DATABASE_PORT=5432

POSTGRES_DB=servermanagerbot
POSTGRES_USER=smbuser
POSTGRES_PASSWORD=${PG_PASSWORD}
PGPORT=5432

TELEGRAM_API_TOKEN=${BOT_TOKEN}
TELEGRAM_ADMINS_ID=${ADMIN_ID}

TRAFFIC_MONITOR_ENABLED=false
TRAFFIC_MONITOR_ALERT_PERCENT=80
EOF
    chmod 600 "$INSTALL_DIR/.env"
    log ".env file created."
else
    log "Preserving existing .env file."
fi

mkdir -p "$INSTALL_DIR/data"

header "Pulling and starting services"

log "Pulling Docker image from Docker Hub..."
docker compose pull

log "Starting services..."
docker compose up -d

header "Waiting for database"

MAX_WAIT=60
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if docker compose exec -T postgres pg_isready -U smbuser -d servermanagerbot >/dev/null 2>&1; then
        log "Database is ready."
        break
    fi
    sleep 2
    WAITED=$((WAITED + 2))
    echo -n "."
done
echo

if [ $WAITED -ge $MAX_WAIT ]; then
    warn "Database readiness check timed out after ${MAX_WAIT}s. Services may still be starting."
fi

header "Installation complete"

echo -e "${GREEN}ServerManagerBot is running!${NC}"
echo ""
echo "  Install directory: $INSTALL_DIR"
echo "  Config file:       $INSTALL_DIR/.env"
echo "  Logs:              cd $INSTALL_DIR && docker compose logs -f"
echo "  Restart:           cd $INSTALL_DIR && docker compose restart"
echo "  Stop:              cd $INSTALL_DIR && docker compose down"
echo "  Update:            cd $INSTALL_DIR && docker compose pull && docker compose up -d"
echo ""
