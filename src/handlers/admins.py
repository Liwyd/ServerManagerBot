from eiogram import Router
from eiogram.filters import Command, IgnoreStateFilter
from eiogram.types import CallbackQuery, Message

from src.db import Admin, AsyncSession, User, UserMessage
from src.keys import AreaType, BotCB, BotKB, TaskType
from src.lang import Dialogs

router = Router()


async def is_admin(db: AsyncSession, user_id: int) -> bool:
    return await User.is_admin(db, user_id)


@router.message(Command("admins"), IgnoreStateFilter())
async def admins_list(message: Message, db: AsyncSession, dbuser: User):
    if not await is_admin(db, dbuser.id):
        return await message.answer("Access Denied")

    from src.config import TELEGRAM_ADMINS_ID
    all_admin_ids = set(TELEGRAM_ADMINS_ID)
    db_admin_ids = await Admin.get_all_user_ids(db)
    all_admin_ids.update(db_admin_ids)

    if not all_admin_ids:
        return await message.answer("No admins configured.")

    lines = []
    for uid in sorted(all_admin_ids):
        user = await User.get_by_id(db, uid)
        name = user.full_name if user else "Unknown"
        source = "env" if uid in TELEGRAM_ADMINS_ID else "bot"
        lines.append(f"• <code>{uid}</code> — {name} [{source}]")

    text = "<b>👑 Admin List</b>\n\n" + "\n".join(lines)
    await message.answer(text)


@router.message(Command("addadmin"), IgnoreStateFilter())
async def add_admin_command(message: Message, db: AsyncSession, dbuser: User):
    if not await is_admin(db, dbuser.id):
        return await message.answer("Access Denied")

    parts = message.text.split()
    if len(parts) < 2:
        return await message.answer("Usage: /addadmin <user_id>")

    try:
        target_id = int(parts[1])
    except ValueError:
        return await message.answer("Invalid user ID.")

    if target_id == dbuser.id:
        return await message.answer("You cannot add yourself as admin.")

    if await User.is_admin(db, target_id):
        return await message.answer("User is already an admin.")

    await Admin.add_admin(db, target_id, added_by=dbuser.id)
    await db.commit()
    await message.answer(f"✅ Admin added: <code>{target_id}</code>")


@router.message(Command("rmadmin"), IgnoreStateFilter())
async def remove_admin_command(message: Message, db: AsyncSession, dbuser: User):
    if not await is_admin(db, dbuser.id):
        return await message.answer("Access Denied")

    parts = message.text.split()
    if len(parts) < 2:
        return await message.answer("Usage: /rmadmin <user_id>")

    try:
        target_id = int(parts[1])
    except ValueError:
        return await message.answer("Invalid user ID.")

    from src.config import TELEGRAM_ADMINS_ID
    if target_id in TELEGRAM_ADMINS_ID:
        return await message.answer("Cannot remove env-configured admin. Edit .env instead.")

    if target_id == dbuser.id:
        return await message.answer("You cannot remove yourself as admin.")

    removed = await Admin.remove_admin(db, target_id)
    await db.commit()

    if removed:
        await message.answer(f"✅ Admin removed: <code>{target_id}</code>")
    else:
        await message.answer("User is not a bot-managed admin.")
