from eiogram import Router
from eiogram.filters import StateFilter, Text
from eiogram.state import State, StateGroup, StateManager
from eiogram.types import CallbackQuery, Message

from src.db import AsyncSession
from src.keys import AreaType, BotCB, BotKB, StepType, TaskType
from src.lang import Dialogs
from src.utils.depends import GetHetzner, ShouldBeOwner

router = Router()


class FloatingIPUpdateForm(StateGroup):
    approval = State()
    input = State()
    select = State()


@router.callback_query(BotCB.filter(area=AreaType.FLOATING_IP, task=TaskType.UPDATE))
async def floating_ips_update(
    callback_query: CallbackQuery,
    callback_data: BotCB,
    db: AsyncSession,
    state: StateManager,
    hetzner: GetHetzner,
    __: ShouldBeOwner,
):
    kb = BotKB.floating_ips_back(id=callback_data.target)
    floating_ip = await hetzner.get_floating_ip_by_id(int(callback_data.target))
    if not floating_ip:
        return await callback_query.message.edit(text=Dialogs.FLOATING_IPS_NOT_FOUND, reply_markup=kb)
    match callback_data.step:
        case StepType.FLOATING_IPS_DELETE | StepType.FLOATING_IPS_UNASSIGN:
            text = Dialogs.ACTIONS_CONFIRM
            _state = FloatingIPUpdateForm.approval
            kb = BotKB.approval(area=AreaType.FLOATING_IP, task=TaskType.UPDATE)
        case StepType.FLOATING_IPS_REMARK:
            text = Dialogs.FLOATING_IPS_ENTER_REMARK
            _state = FloatingIPUpdateForm.input
        case StepType.FLOATING_IPS_ASSIGN:
            servers = await hetzner.get_servers()
            if not servers:
                return await callback_query.answer(text=Dialogs.SERVERS_NOT_FOUND, show_alert=True)
            text = Dialogs.FLOATING_IPS_SELECT_SERVER
            _state = FloatingIPUpdateForm.select
            kb = BotKB.floating_ips_select_server(servers=servers, target=floating_ip.id)
        case StepType.FLOATING_IPS_CHANGE_DNS:
            text = Dialogs.FLOATING_IPS_ENTER_DNS
            _state = FloatingIPUpdateForm.input
        case _:
            return await callback_query.answer(text="Invalid step!", show_alert=True)
    await state.upsert_context(db=db, state=_state, step=callback_data.step, target=callback_data.target)
    return await callback_query.message.edit(text=text, reply_markup=kb)


@router.message(StateFilter(FloatingIPUpdateForm.input), Text())
async def input_handler(
    message: Message,
    db: AsyncSession,
    state: StateManager,
    hetzner: GetHetzner,
    state_data: dict,
    __: ShouldBeOwner,
):
    floating_ip = await hetzner.get_floating_ip_by_id(int(state_data["target"]))
    if not floating_ip:
        return await message.answer(text=Dialogs.FLOATING_IPS_NOT_FOUND)

    match state_data["step"]:
        case StepType.FLOATING_IPS_REMARK:
            await hetzner.update_floating_ip(floating_ip, description=message.text)
        case StepType.FLOATING_IPS_CHANGE_DNS:
            await hetzner.change_floating_ip_dns_ptr(floating_ip, floating_ip.ip, message.text)
        case _:
            return await message.answer(text="Invalid step!", reply_markup=BotKB.floating_ips_back(id=floating_ip.id))

    await state.clear_state(db=db)
    return await message.answer(
        text=Dialogs.FLOATING_IPS_UPDATE_SUCCESS, reply_markup=BotKB.floating_ips_back(id=floating_ip.id)
    )


@router.callback_query(
    StateFilter(FloatingIPUpdateForm.approval), BotCB.filter(area=AreaType.FLOATING_IP, task=TaskType.UPDATE)
)
async def approval_handler(
    callback_query: CallbackQuery,
    callback_data: BotCB,
    db: AsyncSession,
    state: StateManager,
    hetzner: GetHetzner,
    state_data: dict,
    __: ShouldBeOwner,
):
    if not callback_data.is_approve:
        return await callback_query.message.edit(text=Dialogs.ACTIONS_CANCELLED, reply_markup=BotKB.floating_ips_back())

    floating_ip = await hetzner.get_floating_ip_by_id(int(state_data["target"]))
    if not floating_ip:
        return await callback_query.answer(text=Dialogs.FLOATING_IPS_NOT_FOUND, show_alert=True)

    kb = BotKB.floating_ips_back(id=floating_ip.id)
    match state_data["step"]:
        case StepType.FLOATING_IPS_DELETE:
            await hetzner.delete_floating_ip(floating_ip)
            kb = BotKB.floating_ips_back()
        case StepType.FLOATING_IPS_UNASSIGN:
            await callback_query.message.edit(text=Dialogs.ACTIONS_WAITING)
            if not floating_ip.server_id:
                return await callback_query.answer(text=Dialogs.FLOATING_IPS_NOT_FOUND, show_alert=True)
            await hetzner.unassign_floating_ip(floating_ip)

    await state.clear_state(db=db)
    return await callback_query.message.edit(text=Dialogs.FLOATING_IPS_UPDATE_SUCCESS, reply_markup=kb)


@router.callback_query(StateFilter(FloatingIPUpdateForm.select), BotCB.filter(area=AreaType.FLOATING_IP, task=TaskType.UPDATE))
async def select_handler(
    callback_query: CallbackQuery,
    callback_data: BotCB,
    db: AsyncSession,
    state: StateManager,
    hetzner: GetHetzner,
    state_data: dict,
    __: ShouldBeOwner,
):
    floating_ip = await hetzner.get_floating_ip_by_id(int(state_data["target"]))
    if not floating_ip:
        return await callback_query.answer(text=Dialogs.FLOATING_IPS_NOT_FOUND, show_alert=True)

    server = await hetzner.get_server_by_id(int(callback_data.target))
    if not server:
        return await callback_query.answer(text=Dialogs.SERVERS_NOT_FOUND, show_alert=True)

    await hetzner.assign_floating_ip(floating_ip, server)

    await state.clear_state(db=db)
    return await callback_query.message.edit(
        text=Dialogs.FLOATING_IPS_UPDATE_SUCCESS, reply_markup=BotKB.floating_ips_back(id=floating_ip.id)
    )
