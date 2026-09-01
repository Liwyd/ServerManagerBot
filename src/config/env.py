import os

from dotenv import load_dotenv

load_dotenv(override=False)

### Develop Settings
DEBUG = os.environ.get("DEBUG", "false").lower() in ("true", "1", "yes")

### Database Settings
DATABASE_USERNAME = os.environ.get("DATABASE_USERNAME", "")
DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD", "")
DATABASE_HOST = os.environ.get("DATABASE_HOST", "localhost")
DATABASE_PORT = int(os.environ.get("DATABASE_PORT", "5432"))
DATABASE_NAME = os.environ.get("DATABASE_NAME", "")

from sqlalchemy import URL

DATABASE_URL = URL.create(
    drivername="postgresql+asyncpg",
    username=DATABASE_USERNAME,
    password=DATABASE_PASSWORD,
    host=DATABASE_HOST,
    port=DATABASE_PORT,
    database=DATABASE_NAME,
)

SQLALCHEMY_DATABASE_URL = DATABASE_URL.render_as_string(hide_password=False)


### Bot Settings
TELEGRAM_API_TOKEN = os.environ.get("TELEGRAM_API_TOKEN", "")

_admin_ids_raw = os.environ.get("TELEGRAM_ADMINS_ID", "")
TELEGRAM_ADMINS_ID = [int(x.strip()) for x in _admin_ids_raw.split(",") if x.strip()] if _admin_ids_raw else []

### Traffic Monitor Settings
TRAFFIC_MONITOR_ENABLED = os.environ.get("TRAFFIC_MONITOR_ENABLED", "false").lower() in ("true", "1", "yes")
TRAFFIC_MONITOR_ALERT_PERCENT = int(os.environ.get("TRAFFIC_MONITOR_ALERT_PERCENT", "80"))
