<p align="center">
  <a href="https://www.hetzner.com/cloud">
    <img src="https://raw.githubusercontent.com/hetznercloud/csi-driver/main/docs/img/hetzner_logo.png" width="120" alt="Hetzner Cloud">
  </a>
</p>

<h1 align="center">
  <img src="https://img.shields.io/badge/%E2%9A%99%EF%B8%8F-ServerManagerBot-0066cc?style=for-the-badge&logo=telegram&logoColor=white" alt="ServerManagerBot">
</h1>

<p align="center">
  <b>Full-stack Hetzner Cloud management via Telegram bot & CLI</b><br>
  <sub>Servers · Volumes · Floating IPs · Networks · Firewalls · Load Balancers · SSH Keys · Certificates · Placement Groups · Primary IPs · Snapshots</sub>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/Hetzner-2C6EE0?style=flat&logo=hetzner&logoColor=white" alt="Hetzner">
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat" alt="License">
</p>

---

## Features

### Compute
- **Servers** — Create, power on/off, reboot, rebuild, reset, reset password, upgrade, rename, delete
- **Snapshots** — Create, restore, delete, rename
- **Placement Groups** — Create, rename, delete

### Networking
- **Primary IPs** — Create, assign/unassign, rename, reverse DNS, delete
- **Floating IPs** — Create, assign/unassign, reverse DNS, rename, delete
- **Networks** — Create, add/remove subnets, add/remove routes, rename, delete
- **Firewalls** — Create, apply to servers, remove from servers, rename, delete
- **Load Balancers** — Create, add/remove targets, rename, delete

### Storage
- **Volumes** — Create, attach, detach, resize, rename, delete

### Security
- **SSH Keys** — Add, rename, delete
- **Certificates** — Upload custom or managed (Let's Encrypt), rename, delete

### Management
- **Multi-client** — Multiple Hetzner API tokens with per-client access control
- **Multi-admin** — Env-based + bot-managed admin system
- **Traffic Monitoring** — Hourly checks with configurable alert threshold
- **Access Control** — Grant/revoke server access to specific Telegram users per client

---

## Quick Install

```bash
curl -fsSL https://raw.githubusercontent.com/Liwyd/ServerManagerBot/master/install.sh -o /tmp/install.sh && sudo bash /tmp/install.sh
```

## Updating

```bash
sudo bash /opt/servermanagerbot/install.sh --update
```

> Auto-backups `.env` and database, runs migrations, rolls back on failure, cleans old Docker images.

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_USERNAME` | Yes | `smbuser` | PostgreSQL username |
| `DATABASE_PASSWORD` | Yes | — | PostgreSQL password |
| `DATABASE_NAME` | Yes | `servermanagerbot` | PostgreSQL database |
| `DATABASE_HOST` | Yes | `localhost` | PostgreSQL host |
| `DATABASE_PORT` | Yes | `5432` | PostgreSQL port |
| `POSTGRES_DB` | Yes | `servermanagerbot` | Container database |
| `POSTGRES_USER` | Yes | `smbuser` | Container user |
| `POSTGRES_PASSWORD` | Yes | — | Container password |
| `PGPORT` | No | `5432` | Container port |
| `TELEGRAM_API_TOKEN` | Yes | — | Bot token from @BotFather |
| `TELEGRAM_ADMINS_ID` | Yes | — | Comma-separated admin user IDs |
| `TRAFFIC_MONITOR_ENABLED` | No | `false` | Enable traffic alerts |
| `TRAFFIC_MONITOR_ALERT_PERCENT` | No | `80` | Alert threshold |

---

## Manual Installation

### Prerequisites
- Docker & Docker Compose v2
- Git

### Steps

```bash
git clone https://github.com/Liwyd/ServerManagerBot.git /opt/servermanagerbot
cd /opt/servermanagerbot
cp .env.example .env
nano .env
docker compose pull
docker compose up -d
```

---

## CLI (`hserver`)

Full-featured terminal CLI for managing all Hetzner resources.

### Setup
```bash
cd /opt/servermanagerbot
uv sync --group cli
```

### Usage
```bash
hserver --help
hserver status                          # Connection status & summary

hserver servers list                    # List all servers
hserver servers get <id>                # Server details
hserver servers create -n my -t cx22 -i ubuntu-22.04
hserver servers power-on <id>
hserver servers power-off <id>
hserver servers reboot <id>
hserver servers rebuild <id> -i ubuntu-24.04
hserver servers rename <id> -n new-name
hserver servers upgrade <id> -t cpx31
hserver servers reset-password <id>
hserver servers delete <id> -y

hserver volumes list
hserver volumes create -n data -s 50
hserver volumes attach <vol_id> <server_id>
hserver volumes detach <id>
hserver volumes resize <id> -s 100
hserver volumes delete <id> -y

hserver floating-ips list
hserver floating-ips create -t ipv4
hserver floating-ips assign <ip_id> <server_id>
hserver floating-ips unassign <id>
hserver floating-ips set-dns <id> -i 1.2.3.4 -d example.com

hserver networks list
hserver networks create -n my-net -r 10.0.0.0/16
hserver networks add-subnet <id> -t cloud -r 10.0.1.0/24 -z fsn1
hserver networks add-route <id> -d 10.100.0.0/16 -g 10.0.0.1

hserver firewalls list
hserver firewalls apply <fw_id> <server_id>
hserver firewalls remove <fw_id> <server_id>

hserver load-balancers list
hserver load-balancers add-target <lb_id> <server_id>
hserver load-balancers remove-target <lb_id> <server_id>

hserver ssh-keys list
hserver ssh-keys create -n my-key -k ~/.ssh/id_ed25519.pub

hserver certificates list
hserver certificates create -n cert --cert-file cert.pem --key-file key.pem
hserver certificates create-managed -n cert -d example.com -d *.example.com

hserver placement-groups list
hserver primary-ips list
hserver snapshots list

hserver clients list
hserver clients add -n prod -t <hetzner-api-token>
hserver clients test <id>
```

All commands support `--client <id>` to target a specific client.

---

## Admin Commands

| Command | Description |
|---------|-------------|
| `/start` | Start/restart the bot |
| `/admins` | List all admins |
| `/addadmin <user_id>` | Add a bot-managed admin |
| `/rmadmin <user_id>` | Remove a bot-managed admin |

Admins can be configured via `TELEGRAM_ADMINS_ID` in `.env` (env admins) or via `/addadmin` (bot admins). Env admins cannot be removed via bot.

---

## Backup & Restore

### Automatic
The update script creates backups at `/opt/servermanagerbot/backups/`:
- `.env` file
- Full PostgreSQL dump

Last 5 backups are kept.

### Manual Backup
```bash
docker compose exec postgres pg_dump -U smbuser servermanagerbot > backup_$(date +%Y%m%d).sql
```

### Restore
```bash
cat backup_YYYYMMDD.sql | docker compose exec -T postgres psql -U smbuser
```

---

## Management

```bash
cd /opt/servermanagerbot

docker compose logs -f          # View logs
docker compose restart          # Restart
docker compose down             # Stop
docker compose ps               # Status
sudo bash install.sh --update   # Update with backup
```

---

## Architecture

```
┌─────────────────────┐     ┌──────────────────┐
│   Telegram Bot      │────▶│   PostgreSQL 15   │
│   (eiogram + async) │     │   (asyncpg)       │
└────────┬────────────┘     └──────────────────┘
         │
         ▼
┌─────────────────────┐
│   Hetzner Cloud API │
│   (hcloud SDK)      │
└─────────────────────┘
```

- **Bot**: Python 3.11, asyncio, eiogram 2.0, SQLAlchemy 2.0
- **CLI**: click + rich for terminal UI
- **API**: hcloud 2.5.4 (async-wrapped)
- **Deploy**: Docker Compose, host networking

---

## License

MIT
