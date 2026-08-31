# ServerManagerBot

Telegram bot for managing Hetzner Cloud servers, snapshots, and primary IPs.

## Features

- **Server Management**: Create, reboot, rebuild, power on/off, rename, upgrade, and delete servers
- **Snapshot Management**: Create, restore, delete, and rename snapshots
- **Primary IP Management**: Assign, unassign, rename, and delete primary IPs
- **Client Management**: Add multiple Hetzner API tokens, manage per-client server access
- **Traffic Monitoring**: Hourly checks that alert admins when server traffic exceeds threshold
- **Access Control**: Grant/revoke server access to specific Telegram users per client

## Quick Install

```bash
curl -fsSL https://raw.githubusercontent.com/Liwyd/ServerManagerBot/master/install.sh | sudo bash
```

The installer will:
- Install Docker if not present
- Pull the pre-built image from Docker Hub (`liwyd/servermanagerbot`)
- Create configuration with generated secure passwords
- Start all services

## Manual Installation

### Prerequisites

- Docker and Docker Compose v2
- Git

### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/Liwyd/ServerManagerBot.git /opt/servermanagerbot
   cd /opt/servermanagerbot
   ```

2. Create your `.env` file:
   ```bash
   cp .env.example .env
   nano .env
   ```

3. Configure the required variables:
   - `TELEGRAM_API_TOKEN` - Your bot token from @BotFather
   - `TELEGRAM_ADMINS_ID` - Your Telegram user ID
   - `DATABASE_PASSWORD` - Database password (generate a strong one)
   - `POSTGRES_PASSWORD` - Must match `DATABASE_PASSWORD`

4. Pull and start the services:
   ```bash
   docker compose pull
   docker compose up -d
   ```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_USERNAME` | Yes | `smbuser` | PostgreSQL username |
| `DATABASE_PASSWORD` | Yes | - | PostgreSQL password |
| `DATABASE_NAME` | Yes | `servermanagerbot` | PostgreSQL database name |
| `DATABASE_HOST` | Yes | `localhost` | PostgreSQL host |
| `DATABASE_PORT` | Yes | `5432` | PostgreSQL port |
| `POSTGRES_DB` | Yes | `servermanagerbot` | PostgreSQL container database |
| `POSTGRES_USER` | Yes | `smbuser` | PostgreSQL container user |
| `POSTGRES_PASSWORD` | Yes | - | PostgreSQL container password (must match DATABASE_PASSWORD) |
| `PGPORT` | No | `5432` | PostgreSQL container port |
| `TELEGRAM_API_TOKEN` | Yes | - | Telegram bot token |
| `TELEGRAM_ADMINS_ID` | Yes | - | Comma-separated admin user IDs |
| `TRAFFIC_MONITOR_ENABLED` | No | `false` | Enable traffic monitoring |
| `TRAFFIC_MONITOR_ALERT_PERCENT` | No | `80` | Alert threshold percentage |

## Management

```bash
cd /opt/servermanagerbot

# View logs
docker compose logs -f

# Restart services
docker compose restart

# Stop services
docker compose down

# Update
git pull && docker compose pull && docker compose up -d

# Check status
docker compose ps
```

## Data Storage

- PostgreSQL data: Docker volume `servermanagerbot_postgres_data`
- Configuration: `/opt/servermanagerbot/.env`

## Backup

```bash
docker compose exec postgres pg_dumpall -U smbuser > backup_$(date +%Y%m%d).sql
```

## Restore

```bash
cat backup_YYYYMMDD.sql | docker compose exec -T postgres psql -U smbuser
```

## Architecture

- **ServerManagerBot**: Python 3.11 async Telegram bot (eiogram + SQLAlchemy + asyncpg)
- **PostgreSQL 15**: Database backend
- Both services use host networking on configurable ports

## Tech Stack

- Python 3.11+ with asyncio
- Telegram Bot via eiogram
- Hetzner Cloud API via hcloud
- PostgreSQL with asyncpg + SQLAlchemy
- Alembic for database migrations
- APScheduler for cron tasks
- Docker for deployment

## License

MIT
