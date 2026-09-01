from eiogram import Router
from eiogram.filters import StateFilter, Text
from eiogram.state import State, StateGroup, StateManager
from eiogram.types import CallbackQuery, Message

from src.db import AsyncSession, UserMessage
from src.keys import AreaType, BotCB, BotKB, TaskType
from src.lang import Dialogs
from src.utils.depends import GetHetzner, ShouldBeOwner

router = Router()


class FloatingIPCreateForm(StateGroup):
    remark = State()
    location = State()
    server = State()


@router.callback_query(BotCB.filter(area=AreaType.FLOATING_IP, task=TaskType.CREATE))
async def floating_ips_create(
    callback_query: CallbackQuery, callback_data: BotCB, db: AsyncSession, state: StateManager, __: ShouldBeOwner
):
    await state.upsert_context(db=db, state=FloatingIPCreateForm.remark, ip_type=callback_data.target)
    return await callback_query.message.edit(text=Dialogs.FLOATING_IPS_ENTER_REMARK, reply_markup=BotKB.floating_ips_back())


@router.message(StateFilter(FloatingIPCreateForm.remark), Text())
async def remark_handler(
    message: Message, db: AsyncSession, state: StateManager, hetzner: GetHetzner, state_data: dict, __: ShouldBeOwner
):
    locations = await hetzner.get_locations()
    if not locations:
        update = await message.answer(text=Dialogs.FLOATING_IPS_SELECT_LOCATION)
        return await UserMessage.add(update)
    await state.upsert_context(db=db, state=FloatingIPCreateForm.location, remark=message.text)
    update = await message.answer(
        text=Dialogs.FLOATING_IPS_SELECT_LOCATION, reply_markup=BotKB.floating_ips_select_location(locations=locations)
    )
    return await UserMessage.clear(update)


@router.callback_query(
    StateFilter(FloatingIPCreateForm.location), BotCB.filter(area=AreaType.FLOATING_IP, task=TaskType.CREATE)
)
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
        return await callback_query.answer(text=Dialogs.FLOATING_IPS_SELECT_LOCATION, show_alert=True)
    servers = await hetzner.get_servers()
    if not servers:
        try:
            response = await hetzner.create_floating_ip(
                description=state_data["remark"], type=state_data["ip_type"], home_location=location
            )
        except Exception:
            return await callback_query.answer(text=Dialogs.FLOATING_IPS_CREATE_FAILED, show_alert=True)
        if not response:
            return await callback_query.answer(text=Dialogs.FLOATING_IPS_CREATE_FAILED, show_alert=True)
        await state.clear_state(db=db)
        update = await callback_query.message.edit(
            text=Dialogs.FLOATING_IPS_CREATE_SUCCESS, reply_markup=BotKB.floating_ips_back(id=response.floating_ip.id)
        )
        return await UserMessage.add(update)
    await state.upsert_context(db=db, state=FloatingIPCreateForm.server, location_id=callback_data.target)
    update = await callback_query.message.edit(
        text=Dialogs.FLOATING_IPS_SELECT_SERVER, reply_markup=BotKB.floating_ips_select_server(servers=servers)
    )
    return await UserMessage.add(update)


@router.callback_query(StateFilter(FloatingIPCreateForm.server), BotCB.filter(area=AreaType.FLOATING_IP, task=TaskType.CREATE))
async def select_server(
    callback_query: CallbackQuery,
    callback_data: BotCB,
    db: AsyncSession,
    state: StateManager,
    state_data: dict,
    hetzner: GetHetzner,
    __: ShouldBeOwner,
):
    location = await hetzner.get_location_by_id(int(state_data["location_id"]))
    if not location:
        return await callback_query.answer(text=Dialogs.FLOATING_IPS_SELECT_LOCATION, show_alert=True)
    server = await hetzner.get_server_by_id(int(callback_data.target))
    if not server:
        return await callback_query.answer(text=Dialogs.SERVERS_NOT_FOUND, show_alert=True)
    try:
        response = await hetzner.create_floating_ip(
            description=state_data["remark"], type=state_data["ip_type"], home_location=location, server=server
        )
    except Exception:
        return await callback_query.answer(text=Dialogs.FLOATING_IPS_CREATE_FAILED, show_alert=True)
    if not response:
        return await callback_query.answer(text=Dialogs.FLOATING_IPS_CREATE_FAILED, show_alert=True)
    await state.clear_state(db=db)
    update = await callback_query.message.edit(
        text=Dialogs.FLOATING_IPS_CREATE_SUCCESS, reply_markup=BotKB.floating_ips_back(id=response.floating_ip.id)
    )
    return await UserMessage.add(update)
