#!/bin/bash
set -e

# ServerManagerBot - Installer, Updater & Uninstaller
# Usage:
#   Install:    curl -fsSL https://raw.githubusercontent.com/Liwyd/ServerManagerBot/master/install.sh -o /tmp/install.sh && sudo bash /tmp/install.sh
#   Update:     sudo bash install.sh --update
#   Uninstall:  sudo bash install.sh --delete

INSTALL_DIR="/opt/servermanagerbot"
REPO_URL="https://github.com/Liwyd/ServerManagerBot.git"
BRANCH="master"
DOCKER_IMAGE="liwyd/servermanagerbot:latest"
BACKUP_DIR="/opt/servermanagerbot/backups"

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

cleanup_old_images() {
    log "Cleaning up old Docker images..."
    # Remove dangling images
    docker image prune -f 2>/dev/null || true
    # Remove old servermanagerbot images (keep last 2)
    local old_images
    old_images=$(docker images "liwyd/servermanagerbot" --format '{{.ID}} {{.CreatedAt}}' | sort -k2 -r | tail -n +3 | awk '{print $1}')
    if [ -n "$old_images" ]; then
        echo "$old_images" | xargs docker rmi 2>/dev/null || true
        log "Old images cleaned up."
    else
        log "No old images to clean up."
    fi
}

backup_database() {
    local backup_file="$1"
    log "Creating database backup..."
    if docker compose exec -T postgres pg_isready -U smbuser -d servermanagerbot >/dev/null 2>&1; then
        docker compose exec -T postgres pg_dump -U smbuser -d servermanagerbot > "$backup_file" 2>/dev/null
        log "Database backup saved to: $backup_file"
        return 0
    else
        warn "Database not reachable, skipping backup."
        return 1
    fi
}

restore_database() {
    local backup_file="$1"
    if [ ! -f "$backup_file" ]; then
        error "Backup file not found: $backup_file"
        return 1
    fi
    log "Restoring database from backup..."
    docker compose exec -T postgres psql -U smbuser -d servermanagerbot < "$backup_file" 2>/dev/null
    log "Database restored."
}

rollback_update() {
    local backup_dir="$1"
    error "Update failed. Rolling back..."
    # Restore .env if backed up
    if [ -f "$backup_dir/.env.backup" ]; then
        cp "$backup_dir/.env.backup" "$INSTALL_DIR/.env"
        log "Restored .env from backup."
    fi
    # Restore database if backed up
    if [ -f "$backup_dir/db_backup.sql" ]; then
        restore_database "$backup_dir/db_backup.sql" || true
    fi
    # Restart with old image
    docker compose up -d 2>/dev/null || true
    error "Rollback complete. Please check the logs: cd $INSTALL_DIR && docker compose logs"
    exit 1
}

# Ensure interactive prompts work even when piped
if [ ! -t 0 ] && [ -e /dev/tty ]; then
    exec </dev/tty
fi

# ── Parse arguments ──────────────────────────────────────────

MODE="install"
if [ "$1" = "--update" ] || [ "$1" = "-u" ]; then
    MODE="update"
elif [ "$1" = "--delete" ] || [ "$1" = "-d" ]; then
    MODE="delete"
fi

header "ServerManagerBot - $MODE"

if [ "$EUID" -ne 0 ]; then
    error "This script must be run as root (use sudo)."
    exit 1
fi

# ── DELETE MODE ──────────────────────────────────────────────

if [ "$MODE" = "delete" ]; then
    if [ ! -d "$INSTALL_DIR" ]; then
        error "No installation found at $INSTALL_DIR."
        exit 1
    fi

    warn "This will remove ServerManagerBot and all its data."
    echo -n "Type 'DELETE' to confirm: "
    read -r CONFIRM
    if [ "$CONFIRM" != "DELETE" ]; then
        log "Cancelled."
        exit 0
    fi

    cd "$INSTALL_DIR"
    log "Stopping services..."
    docker compose down -v 2>/dev/null || true

    log "Removing Docker images..."
    docker image prune -f 2>/dev/null || true
    docker images "liwyd/servermanagerbot" -q | xargs docker rmi 2>/dev/null || true

    log "Removing installation directory..."
    cd /
    rm -rf "$INSTALL_DIR"

    header "Delete complete"
    echo -e "${GREEN}ServerManagerBot has been removed.${NC}"
    exit 0
fi

# ── Pre-flight checks ───────────────────────────────────────

OS="$(uname -s)"
ARCH="$(uname -m)"
log "Detected OS: $OS, Architecture: $ARCH"

if ! command_exists docker; then
    if [ "$MODE" = "update" ]; then
        error "Docker is not installed. Cannot update."
        exit 1
    fi
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

# ── UPDATE MODE ──────────────────────────────────────────────

if [ "$MODE" = "update" ]; then
    if [ ! -d "$INSTALL_DIR" ]; then
        error "No installation found at $INSTALL_DIR. Run install instead."
        exit 1
    fi

    cd "$INSTALL_DIR"

    if [ ! -f "$INSTALL_DIR/.env" ]; then
        error ".env file not found at $INSTALL_DIR/.env"
        exit 1
    fi

    # Create backup directory
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_PATH="$BACKUP_DIR/$TIMESTAMP"
    mkdir -p "$BACKUP_PATH"

    # Backup .env
    cp "$INSTALL_DIR/.env" "$BACKUP_PATH/.env.backup"
    log "Backed up .env to $BACKUP_PATH/.env.backup"

    # Backup database
    backup_database "$BACKUP_PATH/db_backup.sql" || true

    # Pull new image
    header "Pulling latest image"
    OLD_IMAGE=$(docker inspect --format='{{.Image}}' servermanagerbot-servermanagerbot-1 2>/dev/null || echo "none")
    if docker compose pull 2>/dev/null; then
        log "New image pulled successfully."
    else
        warn "Could not pull from Docker Hub. Attempting local build..."
        if [ -f "Dockerfile" ]; then
            docker compose build --no-cache 2>/dev/null || rollback_update "$BACKUP_PATH"
            log "Built locally."
        else
            error "No Dockerfile found and no remote image available."
            rollback_update "$BACKUP_PATH"
        fi
    fi

    NEW_IMAGE=$(docker inspect --format='{{.Image}}' servermanagerbot-servermanagerbot-1 2>/dev/null || echo "none")

    # Check if image actually changed
    if [ "$OLD_IMAGE" = "$NEW_IMAGE" ] && [ "$OLD_IMAGE" != "none" ]; then
        log "Image unchanged. Checking for source code updates..."
        git pull origin "$BRANCH" 2>/dev/null || true
        # Rebuild if source changed
        if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
            log "Source code changed, rebuilding..."
            docker compose build --no-cache 2>/dev/null || rollback_update "$BACKUP_PATH"
        else
            log "No changes detected. Nothing to update."
            rm -rf "$BACKUP_PATH"
            exit 0
        fi
    fi

    # Stop old container
    header "Stopping old container"
    docker compose down 2>/dev/null || true

    # Update source code
    header "Updating source code"
    git pull origin "$BRANCH" 2>/dev/null || {
        warn "Git pull failed. Re-cloning..."
        cd /
        rm -rf "$INSTALL_DIR"
        git clone --branch "$BRANCH" "$REPO_URL" "$INSTALL_DIR"
        cd "$INSTALL_DIR"
    }

    # Run migrations
    header "Running database migrations"
    if docker compose up -d postgres 2>/dev/null; then
        sleep 5
        MAX_WAIT=30
        WAITED=0
        while [ $WAITED -lt $MAX_WAIT ]; do
            if docker compose exec -T postgres pg_isready -U smbuser -d servermanagerbot >/dev/null 2>&1; then
                break
            fi
            sleep 2
            WAITED=$((WAITED + 2))
        done
        if [ $WAITED -ge $MAX_WAIT ]; then
            warn "Database not ready, skipping migrations."
        else
            log "Running Alembic migrations..."
            docker compose run --rm servermanagerbot uv run alembic upgrade head 2>/dev/null || {
                warn "Migration failed. The new version may require manual intervention."
                warn "Check logs: cd $INSTALL_DIR && docker compose logs"
            }
        fi
    fi

    # Start all services
    header "Starting updated services"
    docker compose up -d 2>/dev/null || rollback_update "$BACKUP_PATH"

    # Wait for health
    sleep 5
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

    # Verify bot is running
    sleep 3
    if docker compose ps servermanagerbot 2>/dev/null | grep -q "Up"; then
        log "Bot container is running."
    else
        warn "Bot container may not be running. Check logs: cd $INSTALL_DIR && docker compose logs"
    fi

    # Cleanup
    header "Cleaning up"
    cleanup_old_images

    # Keep only last 5 backups
    if [ -d "$BACKUP_DIR" ]; then
        ls -dt "$BACKUP_DIR"/*/ 2>/dev/null | tail -n +6 | xargs rm -rf 2>/dev/null || true
    fi

    header "Update complete"
    echo -e "${GREEN}ServerManagerBot updated successfully!${NC}"
    echo ""
    echo "  Backup saved: $BACKUP_PATH"
    echo "  Update:       hserver update"
    echo "  Logs:         hserver logs -f"
    echo "  Restart:      hserver restart"
    echo "  Stop:         hserver stop"
    echo "  Start:        hserver start"
    echo ""
    exit 0
fi

# ── INSTALL MODE ─────────────────────────────────────────────

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
mkdir -p "$BACKUP_DIR"

header "Pulling and starting services"

BUILD_LOCAL=false
log "Pulling Docker image from Docker Hub..."
if docker compose pull 2>/dev/null; then
    log "Image pulled successfully."
else
    warn "Docker Hub image not found. Building locally..."
    BUILD_LOCAL=true
fi

if [ "$BUILD_LOCAL" = true ]; then
    cp "$INSTALL_DIR/docker-compose.yml" "$INSTALL_DIR/docker-compose.yml.bak"
    sed -i 's|^    image:.*|    build: .|' "$INSTALL_DIR/docker-compose.yml"
    log "Building Docker image locally..."
    docker compose build
    mv "$INSTALL_DIR/docker-compose.yml.bak" "$INSTALL_DIR/docker-compose.yml"
fi

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
echo "  Update:            hserver update"
echo "  Logs:              hserver logs -f"
echo "  Restart:           hserver restart"
echo "  Stop:              hserver stop"
echo "  Uninstall:         hserver uninstall"
echo ""
