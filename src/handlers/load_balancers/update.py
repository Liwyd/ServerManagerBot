from eiogram import Router
from eiogram.filters import StateFilter, Text
from eiogram.state import State, StateGroup, StateManager
from eiogram.types import CallbackQuery, Message

from src.db import AsyncSession
from src.keys import AreaType, BotCB, BotKB, StepType, TaskType
from src.lang import Dialogs
from src.utils.depends import GetHetzner, ShouldBeOwner

router = Router()


class LoadBalancerUpdateForm(StateGroup):
    approval = State()
    input = State()
    select_server = State()
    select_target = State()


@router.callback_query(BotCB.filter(area=AreaType.LOAD_BALANCER, task=TaskType.UPDATE))
async def load_balancers_update(
    callback_query: CallbackQuery,
    callback_data: BotCB,
    db: AsyncSession,
    state: StateManager,
    hetzner: GetHetzner,
    __: ShouldBeOwner,
):
    kb = BotKB.load_balancers_back(id=callback_data.target)
    load_balancer = await hetzner.get_load_balancer_by_id(int(callback_data.target))
    if not load_balancer:
        return await callback_query.message.edit(text=Dialogs.LOAD_BALANCERS_NOT_FOUND, reply_markup=kb)
    match callback_data.step:
        case StepType.LOAD_BALANCERS_DELETE:
            text = Dialogs.ACTIONS_CONFIRM
            _state = LoadBalancerUpdateForm.approval
            kb = BotKB.approval(area=AreaType.LOAD_BALANCER, task=TaskType.UPDATE)
        case StepType.LOAD_BALANCERS_REMARK:
            text = Dialogs.LOAD_BALANCERS_ENTER_REMARK
            _state = LoadBalancerUpdateForm.input
        case StepType.LOAD_BALANCERS_ADD_TARGET:
            servers = await hetzner.get_servers()
            if not servers:
                return await callback_query.answer(text=Dialogs.SERVERS_NOT_FOUND, show_alert=True)
            text = Dialogs.LOAD_BALANCERS_SELECT_SERVER
            _state = LoadBalancerUpdateForm.select_server
            kb = BotKB.load_balancers_select_server(servers=servers, task=TaskType.UPDATE, target=load_balancer.id)
        case StepType.LOAD_BALANCERS_DEL_TARGET:
            if not load_balancer.targets:
                return await callback_query.answer(text=Dialogs.LOAD_BALANCERS_NOT_FOUND, show_alert=True)
            text = Dialogs.LOAD_BALANCERS_SELECT_SERVER
            _state = LoadBalancerUpdateForm.select_target
            kb = BotKB.load_balancers_select_target(targets=load_balancer.targets, lb_id=load_balancer.id)
        case _:
            return await callback_query.answer(text="Invalid step!", show_alert=True)
    await state.upsert_context(db=db, state=_state, step=callback_data.step, target=callback_data.target)
    return await callback_query.message.edit(text=text, reply_markup=kb)


@router.message(StateFilter(LoadBalancerUpdateForm.input), Text())
async def input_handler(
    message: Message,
    db: AsyncSession,
    state: StateManager,
    hetzner: GetHetzner,
    state_data: dict,
    __: ShouldBeOwner,
):
    load_balancer = await hetzner.get_load_balancer_by_id(int(state_data["target"]))
    if not load_balancer:
        return await message.answer(text=Dialogs.LOAD_BALANCERS_NOT_FOUND)

    match state_data["step"]:
        case StepType.LOAD_BALANCERS_REMARK:
            await hetzner.update_load_balancer(load_balancer, name=message.text)
        case _:
            return await message.answer(text="Invalid step!", reply_markup=BotKB.load_balancers_back(id=load_balancer.id))

    await state.clear_state(db=db)
    return await message.answer(
        text=Dialogs.LOAD_BALANCERS_UPDATE_SUCCESS, reply_markup=BotKB.load_balancers_back(id=load_balancer.id)
    )


@router.callback_query(
    StateFilter(LoadBalancerUpdateForm.approval), BotCB.filter(area=AreaType.LOAD_BALANCER, task=TaskType.UPDATE)
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
        return await callback_query.message.edit(text=Dialogs.ACTIONS_CANCELLED, reply_markup=BotKB.load_balancers_back())

    load_balancer = await hetzner.get_load_balancer_by_id(int(state_data["target"]))
    if not load_balancer:
        return await callback_query.answer(text=Dialogs.LOAD_BALANCERS_NOT_FOUND, show_alert=True)

    kb = BotKB.load_balancers_back(id=load_balancer.id)
    match state_data["step"]:
        case StepType.LOAD_BALANCERS_DELETE:
            await hetzner.delete_load_balancer(load_balancer)
            kb = BotKB.load_balancers_back()

    await state.clear_state(db=db)
    return await callback_query.message.edit(text=Dialogs.LOAD_BALANCERS_UPDATE_SUCCESS, reply_markup=kb)


@router.callback_query(
    StateFilter(LoadBalancerUpdateForm.select_server), BotCB.filter(area=AreaType.LOAD_BALANCER, task=TaskType.UPDATE)
)
async def select_server_handler(
    callback_query: CallbackQuery,
    callback_data: BotCB,
    db: AsyncSession,
    state: StateManager,
    hetzner: GetHetzner,
    state_data: dict,
    __: ShouldBeOwner,
):
    load_balancer = await hetzner.get_load_balancer_by_id(int(state_data["target"]))
    if not load_balancer:
        return await callback_query.answer(text=Dialogs.LOAD_BALANCERS_NOT_FOUND, show_alert=True)

    server = await hetzner.get_server_by_id(int(callback_data.target))
    if not server:
        return await callback_query.answer(text=Dialogs.SERVERS_NOT_FOUND, show_alert=True)

    from hcloud.load_balancers.domain import LoadBalancerTarget

    target = LoadBalancerTarget(type="server", server=server)
    await hetzner.add_load_balancer_target(load_balancer, target)

    await state.clear_state(db=db)
    return await callback_query.message.edit(
        text=Dialogs.LOAD_BALANCERS_UPDATE_SUCCESS, reply_markup=BotKB.load_balancers_back(id=load_balancer.id)
    )


@router.callback_query(
    StateFilter(LoadBalancerUpdateForm.select_target), BotCB.filter(area=AreaType.LOAD_BALANCER, task=TaskType.UPDATE)
)
async def select_target_handler(
    callback_query: CallbackQuery,
    callback_data: BotCB,
    db: AsyncSession,
    state: StateManager,
    hetzner: GetHetzner,
    state_data: dict,
    __: ShouldBeOwner,
):
    load_balancer = await hetzner.get_load_balancer_by_id(int(state_data["target"]))
    if not load_balancer:
        return await callback_query.answer(text=Dialogs.LOAD_BALANCERS_NOT_FOUND, show_alert=True)

    server = await hetzner.get_server_by_id(int(callback_data.target))
    if not server:
        return await callback_query.answer(text=Dialogs.SERVERS_NOT_FOUND, show_alert=True)

    from hcloud.load_balancers.domain import LoadBalancerTarget

    target = LoadBalancerTarget(type="server", server=server)
    await hetzner.remove_load_balancer_target(load_balancer, target)

    await state.clear_state(db=db)
    return await callback_query.message.edit(
        text=Dialogs.LOAD_BALANCERS_UPDATE_SUCCESS, reply_markup=BotKB.load_balancers_back(id=load_balancer.id)
    )
