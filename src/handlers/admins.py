from eiogram import Router
from eiogram.filters import IgnoreStateFilter, StateFilter, Text
from eiogram.state import State, StateGroup, StateManager
from eiogram.types import CallbackQuery, Message

from src.db import Admin, AsyncSession, User, UserMessage
from src.keys import AreaType, BotCB, BotKB, TaskType
from src.lang import Dialogs

router = Router()


class AdminForm(StateGroup):
    add = State()


@router.callback_query(BotCB.filter(area=AreaType.ADMIN, task=TaskType.MENU), IgnoreStateFilter())
async def admins_menu(callback_query: CallbackQuery, db: AsyncSession, dbuser: User):
    if not await User.is_admin(db, dbuser.id):
        return await callback_query.answer("Access Denied", show_alert=True)
    return await callback_query.message.edit(
        text=Dialogs.ADMINS_MENU, reply_markup=BotKB.admins_menu()
    )


@router.callback_query(BotCB.filter(area=AreaType.ADMIN, task=TaskType.LIST), IgnoreStateFilter())
async def admins_list(callback_query: CallbackQuery, db: AsyncSession, dbuser: User):
    if not await User.is_admin(db, dbuser.id):
        return await callback_query.answer("Access Denied", show_alert=True)

    from src.config import TELEGRAM_ADMINS_ID

    all_admins = []
    for uid in sorted(set(TELEGRAM_ADMINS_ID)):
        user = await User.get_by_id(db, uid)
        name = user.full_name if user else "Unknown"
        all_admins.append({"user_id": uid, "name": name, "source": "env"})

    db_admin_ids = await Admin.get_all_user_ids(db)
    for uid in sorted(db_admin_ids):
        if uid not in set(TELEGRAM_ADMINS_ID):
            user = await User.get_by_id(db, uid)
            name = user.full_name if user else "Unknown"
            all_admins.append({"user_id": uid, "name": name, "source": "bot"})

    if not all_admins:
        return await callback_query.answer("No admins configured.", show_alert=True)

    lines = []
    for a in all_admins:
        lines.append(f"• <code>{a['user_id']}</code> — {a['name']} [{a['source']}]")

    text = Dialogs.ADMINS_LIST.format(admins="\n".join(lines))
    return await callback_query.message.edit(
        text=text, reply_markup=BotKB.admins_list(all_admins)
    )


@router.callback_query(BotCB.filter(area=AreaType.ADMIN, task=TaskType.CREATE), IgnoreStateFilter())
async def admins_add_start(callback_query: CallbackQuery, db: AsyncSession, state: StateManager, dbuser: User):
    if not await User.is_admin(db, dbuser.id):
        return await callback_query.answer("Access Denied", show_alert=True)
    await state.upsert_context(db=db, state=AdminForm.add)
    update = await callback_query.message.edit(
        text=Dialogs.ADMINS_ADD_PROMPT, reply_markup=BotKB.admins_menu()
    )
    return await UserMessage.clear(update, keep_current=True)


@router.message(StateFilter(AdminForm.add), Text())
async def admins_add_confirm(message: Message, db: AsyncSession, state: StateManager, dbuser: User):
    if not await User.is_admin(db, dbuser.id):
        return await message.answer("Access Denied")

    try:
        target_id = int(message.text.strip())
    except ValueError:
        update = await message.answer(text=Dialogs.ADMINS_INVALID_ID)
        return await UserMessage.add(update)

    if target_id == dbuser.id:
        update = await message.answer(text=Dialogs.ADMINS_CANNOT_ADD_SELF)
        return await UserMessage.add(update)

    if await User.is_admin(db, target_id):
        update = await message.answer(text=Dialogs.ADMINS_ALREADY_EXISTS)
        return await UserMessage.add(update)

    await Admin.add_admin(db, target_id, added_by=dbuser.id)
    await db.commit()
    await state.clear_state(db=db)

    update = await message.answer(text=Dialogs.ADMINS_ADDED.format(user_id=target_id))
    return await UserMessage.clear(update)


@router.callback_query(BotCB.filter(area=AreaType.ADMIN, task=TaskType.DELETE), IgnoreStateFilter())
async def admins_remove(callback_query: CallbackQuery, callback_data: BotCB, db: AsyncSession, dbuser: User):
    if not await User.is_admin(db, dbuser.id):
        return await callback_query.answer("Access Denied", show_alert=True)

    target_id = int(callback_data.target)

    if target_id == dbuser.id:
        return await callback_query.answer(Dialogs.ADMINS_CANNOT_REMOVE_SELF, show_alert=True)

    from src.config import TELEGRAM_ADMINS_ID
    if target_id in TELEGRAM_ADMINS_ID:
        return await callback_query.answer(Dialogs.ADMINS_CANNOT_REMOVE_ENV, show_alert=True)

    removed = await Admin.remove_admin(db, target_id)
    await db.commit()

    if removed:
        await callback_query.answer(Dialogs.ADMINS_REMOVED.format(user_id=target_id))
    else:
        return await callback_query.answer(Dialogs.ADMINS_NOT_FOUND, show_alert=True)

    admins = await Admin.get_all_user_ids(db)
    if not admins:
        return await callback_query.message.edit(
            text=Dialogs.ADMINS_MENU, reply_markup=BotKB.admins_menu()
        )

    return await admins_list(callback_query, db, dbuser)
