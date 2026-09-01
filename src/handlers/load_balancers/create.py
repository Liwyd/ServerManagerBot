import asyncio

from eiogram import Router
from eiogram.filters import StateFilter, Text
from eiogram.state import State, StateGroup, StateManager
from eiogram.types import CallbackQuery, Message

from src.db import AsyncSession, UserMessage
from src.keys import AreaType, BotCB, BotKB, TaskType
from src.lang import Dialogs
from src.utils.depends import GetHetzner, ShouldBeOwner

router = Router()


class LoadBalancerCreateForm(StateGroup):
    remark = State()
    lb_type = State()
    location = State()


@router.callback_query(BotCB.filter(area=AreaType.LOAD_BALANCER, task=TaskType.CREATE))
async def load_balancers_create(
    callback_query: CallbackQuery, callback_data: BotCB, db: AsyncSession, state: StateManager, __: ShouldBeOwner
):
    await state.upsert_context(db=db, state=LoadBalancerCreateForm.remark)
    return await callback_query.message.edit(text=Dialogs.LOAD_BALANCERS_ENTER_REMARK, reply_markup=BotKB.load_balancers_back())


@router.message(StateFilter(LoadBalancerCreateForm.remark), Text())
async def remark_handler(
    message: Message, db: AsyncSession, state: StateManager, hetzner: GetHetzner, state_data: dict, __: ShouldBeOwner
):
    lb_types = await asyncio.to_thread(hetzner._client.load_balancer_types.get_all)
    if not lb_types:
        update = await message.answer(text=Dialogs.LOAD_BALANCERS_CREATE_FAILED)
        return await UserMessage.add(update)
    await state.upsert_context(db=db, state=LoadBalancerCreateForm.lb_type, remark=message.text)
    update = await message.answer(
        text=Dialogs.LOAD_BALANCERS_SELECT_TYPE, reply_markup=BotKB.load_balancers_select_type(lb_types=lb_types)
    )
    return await UserMessage.clear(update)


@router.callback_query(
    StateFilter(LoadBalancerCreateForm.lb_type), BotCB.filter(area=AreaType.LOAD_BALANCER, task=TaskType.CREATE)
)
async def select_type(
    callback_query: CallbackQuery,
    callback_data: BotCB,
    db: AsyncSession,
    state: StateManager,
    state_data: dict,
    hetzner: GetHetzner,
    __: ShouldBeOwner,
):
    lb_types = await asyncio.to_thread(hetzner._client.load_balancer_types.get_all)
    selected_type = None
    for lb_type in lb_types:
        if lb_type.id == int(callback_data.target):
            selected_type = lb_type
            break
    if not selected_type:
        return await callback_query.answer(text=Dialogs.LOAD_BALANCERS_CREATE_FAILED, show_alert=True)
    locations = await hetzner.get_locations()
    if not locations:
        return await callback_query.answer(text=Dialogs.LOAD_BALANCERS_CREATE_FAILED, show_alert=True)
    await state.upsert_context(db=db, state=LoadBalancerCreateForm.location, lb_type=selected_type.name)
    update = await callback_query.message.edit(
        text=Dialogs.LOAD_BALANCERS_SELECT_LOCATION, reply_markup=BotKB.load_balancers_select_location(locations=locations)
    )
    return await UserMessage.clear(update, keep_current=True)


@router.callback_query(
    StateFilter(LoadBalancerCreateForm.location), BotCB.filter(area=AreaType.LOAD_BALANCER, task=TaskType.CREATE)
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
        return await callback_query.answer(text=Dialogs.LOAD_BALANCERS_CREATE_FAILED, show_alert=True)
    try:
        response = await hetzner.create_load_balancer(
            name=state_data["remark"],
            load_balancer_type=state_data["lb_type"],
            location=location.name,
        )
    except Exception:
        return await callback_query.answer(text=Dialogs.LOAD_BALANCERS_CREATE_FAILED, show_alert=True)
    if not response:
        return await callback_query.answer(text=Dialogs.LOAD_BALANCERS_CREATE_FAILED, show_alert=True)
    await state.clear_state(db=db)
    update = await callback_query.message.edit(
        text=Dialogs.LOAD_BALANCERS_CREATE_SUCCESS, reply_markup=BotKB.load_balancers_back(id=response.load_balancer.id)
    )
    return await UserMessage.add(update)
