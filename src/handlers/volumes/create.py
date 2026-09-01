from eiogram import Router
from eiogram.filters import StateFilter, Text
from eiogram.state import State, StateGroup, StateManager
from eiogram.types import CallbackQuery, Message

from src.db import AsyncSession, UserMessage
from src.keys import AreaType, BotCB, BotKB, TaskType
from src.lang import Dialogs
from src.utils.depends import GetHetzner, ShouldBeOwner

router = Router()


class VolumeCreateForm(StateGroup):
    remark = State()
    size = State()
    location = State()
    server = State()


@router.callback_query(BotCB.filter(area=AreaType.VOLUME, task=TaskType.CREATE))
async def volumes_create(
    callback_query: CallbackQuery, callback_data: BotCB, db: AsyncSession, state: StateManager, __: ShouldBeOwner
):
    await state.upsert_context(db=db, state=VolumeCreateForm.remark)
    return await callback_query.message.edit(text=Dialogs.VOLUMES_ENTER_REMARK, reply_markup=BotKB.volumes_back())


@router.message(StateFilter(VolumeCreateForm.remark), Text())
async def remark_handler(
    message: Message, db: AsyncSession, state: StateManager, hetzner: GetHetzner, state_data: dict, __: ShouldBeOwner
):
    await state.upsert_context(db=db, state=VolumeCreateForm.size, remark=message.text)
    update = await message.answer(text=Dialogs.VOLUMES_ENTER_SIZE, reply_markup=BotKB.volumes_back())
    return await UserMessage.clear(update)


@router.message(StateFilter(VolumeCreateForm.size), Text())
async def size_handler(
    message: Message, db: AsyncSession, state: StateManager, hetzner: GetHetzner, state_data: dict, __: ShouldBeOwner
):
    try:
        size = int(message.text)
        if size < 10:
            raise ValueError
    except ValueError:
        update = await message.answer(text=Dialogs.VOLUMES_ENTER_SIZE, reply_markup=BotKB.volumes_back())
        return await UserMessage.clear(update)

    locations = await hetzner.get_locations()
    if not locations:
        update = await message.answer(text=Dialogs.VOLUMES_NOT_FOUND, reply_markup=BotKB.volumes_back())
        return await UserMessage.add(update)
    await state.upsert_context(db=db, state=VolumeCreateForm.location, size=size)
    update = await message.answer(
        text=Dialogs.VOLUMES_SELECT_LOCATION, reply_markup=BotKB.volumes_select_location(locations=locations)
    )
    return await UserMessage.clear(update)


@router.callback_query(StateFilter(VolumeCreateForm.location), BotCB.filter(area=AreaType.VOLUME, task=TaskType.CREATE))
async def select_location(
    callback_query: CallbackQuery,
    callback_data: BotCB,
    db: AsyncSession,
    state: StateManager,
    state_data: dict,
    hetzner: GetHetzner,
    __: ShouldBeOwner,
):
    location = await hetzner.get_location_by_id(int(callback_data.target))
    if not location:
        return await callback_query.answer(text=Dialogs.VOLUMES_NOT_FOUND, show_alert=True)

    servers = await hetzner.get_servers()
    if servers:
        await state.upsert_context(db=db, state=VolumeCreateForm.server, location_name=location.name)
        kb = BotKB.volumes_select_server(servers=servers, task=TaskType.CREATE)
        update = await callback_query.message.edit(text=Dialogs.VOLUMES_SELECT_SERVER, reply_markup=kb)
        return await UserMessage.add(update)

    try:
        response = await hetzner.create_volume(name=state_data["remark"], size=state_data["size"], location=location)
    except Exception:
        return await callback_query.answer(text=Dialogs.VOLUMES_CREATE_FAILED, show_alert=True)
    if not response:
        return await callback_query.answer(text=Dialogs.VOLUMES_CREATE_FAILED, show_alert=True)
    await state.clear_state(db=db)
    update = await callback_query.message.edit(
        text=Dialogs.VOLUMES_CREATE_SUCCESS, reply_markup=BotKB.volumes_back(id=response.volume.id)
    )
    return await UserMessage.add(update)


@router.callback_query(StateFilter(VolumeCreateForm.server), BotCB.filter(area=AreaType.VOLUME, task=TaskType.CREATE))
async def select_server(
    callback_query: CallbackQuery,
    callback_data: BotCB,
    db: AsyncSession,
    state: StateManager,
    state_data: dict,
    hetzner: GetHetzner,
    __: ShouldBeOwner,
):
    server = await hetzner.get_server_by_id(int(callback_data.target))
    if not server:
        return await callback_query.answer(text=Dialogs.VOLUMES_NOT_FOUND, show_alert=True)

    try:
        response = await hetzner.create_volume(
            name=state_data["remark"],
            size=state_data["size"],
            location=state_data["location_name"],
            server=server,
        )
    except Exception:
        return await callback_query.answer(text=Dialogs.VOLUMES_CREATE_FAILED, show_alert=True)
    if not response:
        return await callback_query.answer(text=Dialogs.VOLUMES_CREATE_FAILED, show_alert=True)
    await state.clear_state(db=db)
    update = await callback_query.message.edit(
        text=Dialogs.VOLUMES_CREATE_SUCCESS, reply_markup=BotKB.volumes_back(id=response.volume.id)
    )
    return await UserMessage.add(update)
