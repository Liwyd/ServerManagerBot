from eiogram import Router
from eiogram.filters import StateFilter, Text
from eiogram.state import State, StateGroup, StateManager
from eiogram.types import CallbackQuery, Message

from src.db import AsyncSession, UserMessage
from src.keys import AreaType, BotCB, BotKB, TaskType
from src.lang import Dialogs
from src.utils.depends import GetHetzner, ShouldBeOwner

router = Router()


class SnapshotCreateForm(StateGroup):
    remark = State()
    server = State()


@router.callback_query(BotCB.filter(area=AreaType.SNAPSHOT, task=TaskType.CREATE))
async def snapshots_create(
    callback_query: CallbackQuery, db: AsyncSession, state: StateManager, hetzner: GetHetzner, __: ShouldBeOwner
):
    servers = await hetzner.get_servers()
    if not servers:
        return await callback_query.answer(text=Dialogs.SNAPSHOTS_SERVERS_NOT_FOUND, show_alert=True)
    await state.upsert_context(db=db, state=SnapshotCreateForm.remark)
    return await callback_query.message.edit(text=Dialogs.SNAPSHOTS_ENTER_REMARK, reply_markup=BotKB.snapshots_back())


@router.message(StateFilter(SnapshotCreateForm.remark), Text())
async def remark_handler(message: Message, db: AsyncSession, state: StateManager, hetzner: GetHetzner, __: ShouldBeOwner):
    servers = await hetzner.get_servers()
    if not servers:
        update = await message.answer(text=Dialogs.SNAPSHOTS_SERVERS_NOT_FOUND)
        return await UserMessage.clear(update)

    await state.upsert_context(db=db, state=SnapshotCreateForm.server, remark=message.text)
    update = await message.answer(
        text=Dialogs.SNAPSHOTS_SELECT_SERVER, reply_markup=BotKB.snapshots_select_server(servers=servers)
    )
    return await UserMessage.clear(update)


@router.callback_query(StateFilter(SnapshotCreateForm.server), BotCB.filter(area=AreaType.SNAPSHOT, task=TaskType.CREATE))
async def server_handler(
    callback_query: CallbackQuery,
    callback_data: BotCB,
    db: AsyncSession,
    state: StateManager,
    hetzner: GetHetzner,
    state_data: dict,
    __: ShouldBeOwner,
):
    server = await hetzner.get_server_by_id(int(callback_data.target))
    if not server:
        return await callback_query.answer(text=Dialogs.SNAPSHOTS_SERVER_NOT_FOUND, show_alert=True)

    try:
        response = await hetzner.create_server_image(server, description=state_data["remark"], type="snapshot")
    except Exception:
        return await callback_query.answer(text=Dialogs.ACTIONS_FAILED, show_alert=True)

    await state.clear_state(db=db)
    return await callback_query.message.edit(
        text=Dialogs.SNAPSHOTS_CREATE_SUCCESS, reply_markup=BotKB.snapshots_back(response.image.id)
    )
