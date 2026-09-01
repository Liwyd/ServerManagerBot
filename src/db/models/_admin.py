from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import select

from ..core import Base


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    added_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)

    @classmethod
    async def get_all_user_ids(cls, db: AsyncSession) -> list[int]:
        result = await db.execute(select(cls.user_id))
        return [row[0] for row in result.all()]

    @classmethod
    async def add_admin(cls, db: AsyncSession, user_id: int, added_by: int) -> "Admin":
        existing = await cls.get_by_user_id(db, user_id)
        if existing:
            return existing
        admin = cls(user_id=user_id, added_by=added_by)
        db.add(admin)
        await db.flush()
        return admin

    @classmethod
    async def remove_admin(cls, db: AsyncSession, user_id: int) -> bool:
        result = await db.execute(select(cls).where(cls.user_id == user_id))
        admin = result.scalars().first()
        if not admin:
            return False
        await db.delete(admin)
        await db.flush()
        return True

    @classmethod
    async def get_by_user_id(cls, db: AsyncSession, user_id: int) -> Optional["Admin"]:
        result = await db.execute(select(cls).where(cls.user_id == user_id))
        return result.scalars().first()

    def __repr__(self) -> str:
        return f"<Admin(user_id={self.user_id})>"
