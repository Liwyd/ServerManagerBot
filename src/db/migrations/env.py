import asyncio
import logging
import time
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from src.config import SQLALCHEMY_DATABASE_URL
from src.db.core import Base

logger = logging.getLogger(__name__)

config = context.config
config.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations(connectable: AsyncEngine) -> None:
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


def _redact_url(url_str: str) -> str:
    """Redact password from database URL for safe logging."""
    try:
        from sqlalchemy import URL as SAURL

        parsed = SAURL.create(url_str)
        if parsed.password:
            return str(parsed.update(password="***"))
    except Exception:
        pass
    return "<unable to redact>"


def run_migrations_online() -> None:
    url_str = config.get_main_option("sqlalchemy.url")
    max_retries = 30
    retry_delay = 2

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(
                "Database connection attempt %d/%d (host=%s, port=%s, db=%s)",
                attempt,
                max_retries,
                _get_db_param(url_str, "host"),
                _get_db_param(url_str, "port"),
                _get_db_param(url_str, "database"),
            )
            connectable = create_async_engine(url_str, poolclass=None)
            asyncio.run(run_async_migrations(connectable))
            logger.info("Database migrations completed successfully.")
            return
        except Exception as e:
            error_type = type(e).__name__
            if "Name or service not known" in str(e) or "gaierror" in error_type:
                error_class = "DNS resolution failed"
            elif "Connection refused" in str(e):
                error_class = "Connection refused"
            elif "authentication" in str(e).lower() or "password" in str(e).lower():
                error_class = "Authentication failed"
            elif "does not exist" in str(e).lower():
                error_class = "Database does not exist"
            elif "ssl" in str(e).lower():
                error_class = "SSL error"
            else:
                error_class = error_type

            logger.warning(
                "Database connection attempt %d/%d failed: %s (%s)",
                attempt,
                max_retries,
                error_class,
                str(e)[:200],
            )
            if attempt < max_retries:
                time.sleep(retry_delay)
            else:
                logger.error(
                    "Failed to connect to database after %d attempts. Database host=%s, port=%s, db=%s. Error: %s",
                    max_retries,
                    _get_db_param(url_str, "host"),
                    _get_db_param(url_str, "port"),
                    _get_db_param(url_str, "database"),
                    error_class,
                )
                raise


def _get_db_param(url_str: str, param: str) -> str:
    """Extract a parameter from the database URL for safe logging."""
    try:
        from sqlalchemy import URL as SAURL

        parsed = SAURL.create(url_str)
        return str(getattr(parsed, param, "unknown"))
    except Exception:
        return "unknown"


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
