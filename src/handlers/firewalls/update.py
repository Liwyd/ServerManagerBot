from eiogram import Router
from eiogram.filters import StateFilter, Text
from eiogram.state import State, StateGroup, StateManager
from eiogram.types import CallbackQuery, Message
from hcloud.firewalls.domain import FirewallResource

from src.db import AsyncSession
from src.keys import AreaType, BotCB, BotKB, StepType, TaskType
from src.lang import Dialogs
from src.utils.depends import GetHetzner, ShouldBeOwner

router = Router()


class FirewallUpdateForm(StateGroup):
    approval = State()
    input = State()
    select = State()


@router.callback_query(BotCB.filter(area=AreaType.FIREWALL, task=TaskType.UPDATE))
async def firewalls_update(
    callback_query: CallbackQuery,
    callback_data: BotCB,
    db: AsyncSession,
    state: StateManager,
    hetzner: GetHetzner,
    __: ShouldBeOwner,
):
    kb = BotKB.firewalls_back(id=callback_data.target)
    firewall = await hetzner.get_firewall_by_id(int(callback_data.target))
    if not firewall:
        return await callback_query.message.edit(text=Dialogs.FIREWALLS_NOT_FOUND, reply_markup=kb)
    match callback_data.step:
        case StepType.FIREWALLS_DELETE:
            text = Dialogs.ACTIONS_CONFIRM
            _state = FirewallUpdateForm.approval
            kb = BotKB.approval(area=AreaType.FIREWALL, task=TaskType.UPDATE)
        case StepType.FIREWALLS_REMARK:
            text = Dialogs.FIREWALLS_ENTER_REMARK
            _state = FirewallUpdateForm.input
        case StepType.FIREWALLS_APPLY:
            servers = await hetzner.get_servers()
            if not servers:
                return await callback_query.answer(text=Dialogs.SERVERS_NOT_FOUND, show_alert=True)
            text = "🌍 Select a server to apply the firewall to:"
            _state = FirewallUpdateForm.select
            kb = BotKB.firewalls_select_server(servers=servers, step=StepType.FIREWALLS_APPLY)
        case StepType.FIREWALLS_REMOVE:
            servers = await hetzner.get_servers()
            if not servers:
                return await callback_query.answer(text=Dialogs.SERVERS_NOT_FOUND, show_alert=True)
            applied_server_ids = set()
            if firewall.applied_to:
                for resource in firewall.applied_to:
                    if resource.server:
                        applied_server_ids.add(resource.server.id)
            applied_servers = [s for s in servers if s.id in applied_server_ids]
            if not applied_servers:
                return await callback_query.answer(text=Dialogs.SERVERS_NOT_FOUND, show_alert=True)
            text = "🌍 Select a server to remove the firewall from:"
            _state = FirewallUpdateForm.select
            kb = BotKB.firewalls_select_server(servers=applied_servers, step=StepType.FIREWALLS_REMOVE)
        case _:
            return await callback_query.answer(text="Invalid step!", show_alert=True)
    await state.upsert_context(db=db, state=_state, step=callback_data.step, target=callback_data.target)
    return await callback_query.message.edit(text=text, reply_markup=kb)


@router.message(StateFilter(FirewallUpdateForm.input), Text())
async def input_handler(
    message: Message,
    db: AsyncSession,
    state: StateManager,
    hetzner: GetHetzner,
    state_data: dict,
    __: ShouldBeOwner,
):
    firewall = await hetzner.get_firewall_by_id(int(state_data["target"]))
    if not firewall:
        return await message.answer(text=Dialogs.FIREWALLS_NOT_FOUND)

    match state_data["step"]:
        case StepType.FIREWALLS_REMARK:
            await hetzner.update_firewall(firewall, name=message.text)
        case _:
            return await message.answer(text="Invalid step!", reply_markup=BotKB.firewalls_back(id=firewall.id))

    await state.clear_state(db=db)
    return await message.answer(text=Dialogs.FIREWALLS_UPDATE_SUCCESS, reply_markup=BotKB.firewalls_back(id=firewall.id))


@router.callback_query(StateFilter(FirewallUpdateForm.approval), BotCB.filter(area=AreaType.FIREWALL, task=TaskType.UPDATE))
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
        return await callback_query.message.edit(text=Dialogs.ACTIONS_CANCELLED, reply_markup=BotKB.firewalls_back())

    firewall = await hetzner.get_firewall_by_id(int(state_data["target"]))
    if not firewall:
        return await callback_query.answer(text=Dialogs.FIREWALLS_NOT_FOUND, show_alert=True)

    kb = BotKB.firewalls_back(id=firewall.id)
    match state_data["step"]:
        case StepType.FIREWALLS_DELETE:
            await hetzner.delete_firewall(firewall)
            kb = BotKB.firewalls_back()

    await state.clear_state(db=db)
    return await callback_query.message.edit(text=Dialogs.FIREWALLS_UPDATE_SUCCESS, reply_markup=kb)


@router.callback_query(StateFilter(FirewallUpdateForm.select), BotCB.filter(area=AreaType.FIREWALL, task=TaskType.UPDATE))
async def select_handler(
    callback_query: CallbackQuery,
    callback_data: BotCB,
    db: AsyncSession,
    state: StateManager,
    hetzner: GetHetzner,
    state_data: dict,
    __: ShouldBeOwner,
):
    firewall = await hetzner.get_firewall_by_id(int(state_data["target"]))
    if not firewall:
        return await callback_query.answer(text=Dialogs.FIREWALLS_NOT_FOUND, show_alert=True)

    server = await hetzner.get_server_by_id(int(callback_data.target))
    if not server:
        return await callback_query.answer(text=Dialogs.SERVERS_NOT_FOUND, show_alert=True)

    resource = FirewallResource(type=FirewallResource.TYPE_SERVER, server=server)
    match state_data["step"]:
        case StepType.FIREWALLS_APPLY:
            await hetzner.apply_firewall_to_resources(firewall, resources=[resource])
        case StepType.FIREWALLS_REMOVE:
            await hetzner.remove_firewall_from_resources(firewall, resources=[resource])

    await state.clear_state(db=db)
    return await callback_query.message.edit(
        text=Dialogs.FIREWALLS_UPDATE_SUCCESS, reply_markup=BotKB.firewalls_back(id=firewall.id)
    )
