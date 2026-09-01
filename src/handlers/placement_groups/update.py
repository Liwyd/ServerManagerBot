from eiogram import Router
from eiogram.filters import StateFilter, Text
from eiogram.state import State, StateGroup, StateManager
from eiogram.types import CallbackQuery, Message

from src.db import AsyncSession
from src.keys import AreaType, BotCB, BotKB, StepType, TaskType
from src.lang import Dialogs
from src.utils.depends import GetHetzner, ShouldBeOwner

router = Router()


class PlacementGroupUpdateForm(StateGroup):
    approval = State()
    input = State()


@router.callback_query(BotCB.filter(area=AreaType.PLACEMENT_GROUP, task=TaskType.UPDATE))
async def placement_groups_update(
    callback_query: CallbackQuery,
    callback_data: BotCB,
    db: AsyncSession,
    state: StateManager,
    hetzner: GetHetzner,
    __: ShouldBeOwner,
):
    kb = BotKB.placement_groups_back(id=callback_data.target)
    placement_group = await hetzner.get_placement_group_by_id(int(callback_data.target))
    if not placement_group:
        return await callback_query.message.edit(text=Dialogs.PLACEMENT_GROUPS_NOT_FOUND, reply_markup=kb)
    match callback_data.step:
        case StepType.PLACEMENT_GROUPS_DELETE:
            text = Dialogs.ACTIONS_CONFIRM
            _state = PlacementGroupUpdateForm.approval
            kb = BotKB.approval(area=AreaType.PLACEMENT_GROUP, task=TaskType.UPDATE)
        case StepType.PLACEMENT_GROUPS_REMARK:
            text = Dialogs.PLACEMENT_GROUPS_ENTER_REMARK
            _state = PlacementGroupUpdateForm.input
        case _:
            return await callback_query.answer(text="Invalid step!", show_alert=True)
    await state.upsert_context(db=db, state=_state, step=callback_data.step, target=callback_data.target)
    return await callback_query.message.edit(text=text, reply_markup=kb)


@router.message(StateFilter(PlacementGroupUpdateForm.input), Text())
async def input_handler(
    message: Message,
    db: AsyncSession,
    state: StateManager,
    hetzner: GetHetzner,
    state_data: dict,
    __: ShouldBeOwner,
):
    placement_group = await hetzner.get_placement_group_by_id(int(state_data["target"]))
    if not placement_group:
        return await message.answer(text=Dialogs.PLACEMENT_GROUPS_NOT_FOUND)

    match state_data["step"]:
        case StepType.PLACEMENT_GROUPS_REMARK:
            await hetzner.update_placement_group(placement_group, name=message.text)
        case _:
            return await message.answer(text="Invalid step!", reply_markup=BotKB.placement_groups_back(id=placement_group.id))

    await state.clear_state(db=db)
    return await message.answer(
        text=Dialogs.PLACEMENT_GROUPS_UPDATE_SUCCESS,
        reply_markup=BotKB.placement_groups_back(id=placement_group.id),
    )


@router.callback_query(
    StateFilter(PlacementGroupUpdateForm.approval), BotCB.filter(area=AreaType.PLACEMENT_GROUP, task=TaskType.UPDATE)
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
        return await callback_query.message.edit(text=Dialogs.ACTIONS_CANCELLED, reply_markup=BotKB.placement_groups_back())

    placement_group = await hetzner.get_placement_group_by_id(int(state_data["target"]))
    if not placement_group:
        return await callback_query.answer(text=Dialogs.PLACEMENT_GROUPS_NOT_FOUND, show_alert=True)

    kb = BotKB.placement_groups_back(id=placement_group.id)
    match state_data["step"]:
        case StepType.PLACEMENT_GROUPS_DELETE:
            await hetzner.delete_placement_group(placement_group)
            kb = BotKB.placement_groups_back()

    await state.clear_state(db=db)
    return await callback_query.message.edit(text=Dialogs.PLACEMENT_GROUPS_UPDATE_SUCCESS, reply_markup=kb)
