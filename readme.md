<p align="center">
  <img src="https://raw.githubusercontent.com/hetznercloud/csi-driver/main/docs/img/hetzner_logo.png" width="120" alt="Hetzner">
</p>

<h1 align="center">⚙️ ServerManagerBot</h1>

<p align="center">
  <b>Hetzner Cloud management via Telegram bot & CLI</b>
</p>

---

## Features

**Compute**
- Servers — Create, power on/off, reboot, rebuild, reset, reset password, upgrade, rename, delete
- Snapshots — Create, restore, delete, rename
- Placement Groups — Create, rename, delete

**Networking**
- Primary IPs — Create, assign/unassign, rename, reverse DNS, delete
- Floating IPs — Create, assign/unassign, reverse DNS, rename, delete
- Networks — Create, add/remove subnets, add/remove routes, rename, delete
- Firewalls — Create, apply/remove from servers, rename, delete
- Load Balancers — Create, add/remove targets, rename, delete

**Storage**
- Volumes — Create, attach, detach, resize, rename, delete

**Security**
- SSH Keys — Add, rename, delete
- Certificates — Upload custom or managed (Let's Encrypt), rename, delete

**Management**
- Multi-client — Multiple Hetzner API tokens with per-client access
- Multi-admin — Env-based + bot-managed admin system via inline buttons
- Traffic Monitoring — Hourly checks with configurable alert threshold
- Access Control — Grant/revoke server access per client

---

## Quick Install

```bash
curl -fsSL https://raw.githubusercontent.com/Liwyd/ServerManagerBot/master/install.sh -o /tmp/install.sh && sudo bash /tmp/install.sh
```

## Updating

```bash
hserver update
```

## Uninstalling

```bash
hserver uninstall
```

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

```bash
git clone https://github.com/Liwyd/ServerManagerBot.git /opt/servermanagerbot
cd /opt/servermanagerbot
cp .env.example .env
nano .env
docker compose pull
docker compose up -d
```

---

## CLI

Full terminal CLI for managing all Hetzner resources and the bot itself.

```bash
cd /opt/servermanagerbot
uv sync --group cli
hserver --help
```

---

## Backup & Restore

**Automatic** — Update script saves to `/opt/servermanagerbot/backups/` (last 5 kept)

**Manual**
```bash
docker compose exec postgres pg_dump -U smbuser servermanagerbot > backup.sql
cat backup.sql | docker compose exec -T postgres psql -U smbuser
```

---

## License

MIT
