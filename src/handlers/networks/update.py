from eiogram import Router
from eiogram.filters import StateFilter, Text
from eiogram.state import State, StateGroup, StateManager
from eiogram.types import CallbackQuery, Message
from hcloud.networks.domain import NetworkRoute, NetworkSubnet

from src.db import AsyncSession
from src.keys import AreaType, BotCB, BotKB, StepType, TaskType
from src.lang import Dialogs
from src.utils.depends import GetHetzner, ShouldBeOwner

router = Router()


class NetworkUpdateForm(StateGroup):
    approval = State()
    input = State()
    select_subnet = State()
    select_route = State()
    subnet_type = State()
    subnet_zone = State()


@router.callback_query(BotCB.filter(area=AreaType.NETWORK, task=TaskType.UPDATE))
async def networks_update(
    callback_query: CallbackQuery,
    callback_data: BotCB,
    db: AsyncSession,
    state: StateManager,
    hetzner: GetHetzner,
    __: ShouldBeOwner,
):
    kb = BotKB.networks_back(id=callback_data.target)
    network = await hetzner.get_network_by_id(int(callback_data.target))
    if not network:
        return await callback_query.message.edit(text=Dialogs.NETWORKS_NOT_FOUND, reply_markup=kb)

    match callback_data.step:
        case StepType.NETWORKS_DELETE:
            text = Dialogs.ACTIONS_CONFIRM
            _state = NetworkUpdateForm.approval
            kb = BotKB.approval(area=AreaType.NETWORK, task=TaskType.UPDATE)
        case StepType.NETWORKS_REMARK:
            text = Dialogs.NETWORKS_ENTER_REMARK
            _state = NetworkUpdateForm.input
        case StepType.NETWORKS_ADD_SUBNET:
            text = Dialogs.NETWORKS_ENTER_SUBNET
            _state = NetworkUpdateForm.input
        case StepType.NETWORKS_DEL_SUBNET:
            if not network.subnets:
                return await callback_query.answer(text=Dialogs.NETWORKS_NOT_FOUND, show_alert=True)
            text = Dialogs.NETWORKS_SELECT_SUBNET
            _state = NetworkUpdateForm.select_subnet
            kb = BotKB.networks_select_subnet(subnets=network.subnets, network_id=network.id)
        case StepType.NETWORKS_ADD_ROUTE:
            text = Dialogs.NETWORKS_ENTER_ROUTE
            _state = NetworkUpdateForm.input
        case StepType.NETWORKS_DEL_ROUTE:
            if not network.routes:
                return await callback_query.answer(text=Dialogs.NETWORKS_NOT_FOUND, show_alert=True)
            text = "🛤️ Select a route to delete:"
            _state = NetworkUpdateForm.select_route
            kb = BotKB.networks_select_route(routes=network.routes, network_id=network.id)
        case _:
            return await callback_query.answer(text="Invalid step!", show_alert=True)

    await state.upsert_context(db=db, state=_state, step=callback_data.step, target=callback_data.target)
    return await callback_query.message.edit(text=text, reply_markup=kb)


@router.message(StateFilter(NetworkUpdateForm.input), Text())
async def input_handler(
    message: Message,
    db: AsyncSession,
    state: StateManager,
    hetzner: GetHetzner,
    state_data: dict,
    __: ShouldBeOwner,
):
    network = await hetzner.get_network_by_id(int(state_data["target"]))
    if not network:
        return await message.answer(text=Dialogs.NETWORKS_NOT_FOUND)

    match state_data["step"]:
        case StepType.NETWORKS_REMARK:
            await hetzner.update_network(network, name=message.text)
            await state.clear_state(db=db)
            return await message.answer(text=Dialogs.NETWORKS_UPDATE_SUCCESS, reply_markup=BotKB.networks_back(id=network.id))
        case StepType.NETWORKS_ADD_SUBNET:
            await state.upsert_context(
                db=db, state=NetworkUpdateForm.subnet_type, subnet_ip_range=message.text, target=state_data["target"]
            )
            return await message.answer(
                text=Dialogs.NETWORKS_ENTER_SUBNET_TYPE,
                reply_markup=BotKB.networks_select_subnet_type(network_id=network.id),
            )
        case StepType.NETWORKS_ADD_ROUTE:
            parts = message.text.strip().split()
            if len(parts) != 2:
                return await message.answer(text=Dialogs.NETWORKS_ENTER_ROUTE)
            destination, gateway = parts
            try:
                route = NetworkRoute(destination=destination, gateway=gateway)
                await hetzner.add_route_to_network(network, route)
            except Exception:
                return await message.answer(text=Dialogs.ACTIONS_FAILED)
            await state.clear_state(db=db)
            return await message.answer(text=Dialogs.NETWORKS_UPDATE_SUCCESS, reply_markup=BotKB.networks_back(id=network.id))
        case _:
            return await message.answer(text="Invalid step!", reply_markup=BotKB.networks_back(id=network.id))


@router.callback_query(StateFilter(NetworkUpdateForm.approval), BotCB.filter(area=AreaType.NETWORK, task=TaskType.UPDATE))
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
        return await callback_query.message.edit(text=Dialogs.ACTIONS_CANCELLED, reply_markup=BotKB.networks_back())

    network = await hetzner.get_network_by_id(int(state_data["target"]))
    if not network:
        return await callback_query.answer(text=Dialogs.NETWORKS_NOT_FOUND, show_alert=True)

    kb = BotKB.networks_back(id=network.id)
    match state_data["step"]:
        case StepType.NETWORKS_DELETE:
            await hetzner.delete_network(network)
            kb = BotKB.networks_back()

    await state.clear_state(db=db)
    return await callback_query.message.edit(text=Dialogs.NETWORKS_UPDATE_SUCCESS, reply_markup=kb)


@router.callback_query(StateFilter(NetworkUpdateForm.select_subnet), BotCB.filter(area=AreaType.NETWORK, task=TaskType.UPDATE))
async def select_subnet_handler(
    callback_query: CallbackQuery,
    callback_data: BotCB,
    db: AsyncSession,
    state: StateManager,
    hetzner: GetHetzner,
    state_data: dict,
    __: ShouldBeOwner,
):
    network = await hetzner.get_network_by_id(int(state_data["target"]))
    if not network:
        return await callback_query.answer(text=Dialogs.NETWORKS_NOT_FOUND, show_alert=True)

    parts = callback_data.target.split("|")
    if len(parts) != 2:
        return await callback_query.answer(text="Invalid subnet!", show_alert=True)
    ip_range, network_zone = parts

    subnet = None
    for s in network.subnets:
        if s.ip_range == ip_range and s.network_zone == network_zone:
            subnet = s
            break

    if not subnet:
        return await callback_query.answer(text=Dialogs.NETWORKS_NOT_FOUND, show_alert=True)

    try:
        await hetzner.delete_subnet_from_network(network, subnet)
    except Exception:
        return await callback_query.answer(text=Dialogs.ACTIONS_FAILED, show_alert=True)

    await state.clear_state(db=db)
    return await callback_query.message.edit(
        text=Dialogs.NETWORKS_UPDATE_SUCCESS, reply_markup=BotKB.networks_back(id=network.id)
    )


@router.callback_query(StateFilter(NetworkUpdateForm.select_route), BotCB.filter(area=AreaType.NETWORK, task=TaskType.UPDATE))
async def select_route_handler(
    callback_query: CallbackQuery,
    callback_data: BotCB,
    db: AsyncSession,
    state: StateManager,
    hetzner: GetHetzner,
    state_data: dict,
    __: ShouldBeOwner,
):
    network = await hetzner.get_network_by_id(int(state_data["target"]))
    if not network:
        return await callback_query.answer(text=Dialogs.NETWORKS_NOT_FOUND, show_alert=True)

    parts = callback_data.target.split("|")
    if len(parts) != 2:
        return await callback_query.answer(text="Invalid route!", show_alert=True)
    destination, gateway = parts

    route = None
    for r in network.routes:
        if r.destination == destination and r.gateway == gateway:
            route = r
            break

    if not route:
        return await callback_query.answer(text=Dialogs.NETWORKS_NOT_FOUND, show_alert=True)

    try:
        await hetzner.delete_route_from_network(network, route)
    except Exception:
        return await callback_query.answer(text=Dialogs.ACTIONS_FAILED, show_alert=True)

    await state.clear_state(db=db)
    return await callback_query.message.edit(
        text=Dialogs.NETWORKS_UPDATE_SUCCESS, reply_markup=BotKB.networks_back(id=network.id)
    )


@router.callback_query(StateFilter(NetworkUpdateForm.subnet_type), BotCB.filter(area=AreaType.NETWORK, task=TaskType.UPDATE))
async def subnet_type_handler(
    callback_query: CallbackQuery,
    callback_data: BotCB,
    db: AsyncSession,
    state: StateManager,
    state_data: dict,
    __: ShouldBeOwner,
):
    subnet_type = callback_data.target
    if subnet_type not in ("cloud", "vswitch"):
        return await callback_query.answer(text="Invalid subnet type!", show_alert=True)

    network_id = state_data["target"]
    subnet_ip_range = state_data["subnet_ip_range"]

    await state.upsert_context(db=db, state=NetworkUpdateForm.subnet_zone, subnet_type=subnet_type, target=network_id)
    return await callback_query.message.edit(
        text="🌍 Select the network zone:",
        reply_markup=BotKB.networks_select_network_zone(
            network_id=int(network_id), subnet_ip_range=subnet_ip_range, subnet_type=subnet_type
        ),
    )


@router.callback_query(StateFilter(NetworkUpdateForm.subnet_zone), BotCB.filter(area=AreaType.NETWORK, task=TaskType.UPDATE))
async def subnet_zone_handler(
    callback_query: CallbackQuery,
    callback_data: BotCB,
    db: AsyncSession,
    state: StateManager,
    hetzner: GetHetzner,
    state_data: dict,
    __: ShouldBeOwner,
):
    zone = callback_data.target
    if zone not in ("eu-central", "us-east", "ap-south"):
        return await callback_query.answer(text="Invalid network zone!", show_alert=True)

    network = await hetzner.get_network_by_id(int(state_data["target"]))
    if not network:
        return await callback_query.answer(text=Dialogs.NETWORKS_NOT_FOUND, show_alert=True)

    subnet = NetworkSubnet(
        type=state_data["subnet_type"],
        ip_range=state_data["subnet_ip_range"],
        network_zone=zone,
    )

    try:
        await hetzner.add_subnet_to_network(network, subnet)
    except Exception:
        return await callback_query.answer(text=Dialogs.ACTIONS_FAILED, show_alert=True)

    await state.clear_state(db=db)
    return await callback_query.message.edit(
        text=Dialogs.NETWORKS_UPDATE_SUCCESS, reply_markup=BotKB.networks_back(id=network.id)
    )
