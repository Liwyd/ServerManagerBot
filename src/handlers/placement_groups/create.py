from eiogram import Router
from eiogram.filters import StateFilter, Text
from eiogram.state import State, StateGroup, StateManager
from eiogram.types import CallbackQuery, Message

from src.db import AsyncSession, UserMessage
from src.keys import AreaType, BotCB, BotKB, TaskType
from src.lang import Dialogs
from src.utils.depends import GetHetzner, ShouldBeOwner

router = Router()


class PlacementGroupCreateForm(StateGroup):
    remark = State()
    type = State()


@router.callback_query(BotCB.filter(area=AreaType.PLACEMENT_GROUP, task=TaskType.CREATE))
async def placement_groups_create(
    callback_query: CallbackQuery,
    callback_data: BotCB,
    db: AsyncSession,
    state: StateManager,
    __: ShouldBeOwner,
):
    await state.upsert_context(db=db, state=PlacementGroupCreateForm.remark)
    return await callback_query.message.edit(
        text=Dialogs.PLACEMENT_GROUPS_ENTER_REMARK,
        reply_markup=BotKB.placement_groups_back(),
    )


@router.message(StateFilter(PlacementGroupCreateForm.remark), Text())
async def remark_handler(
    message: Message,
    db: AsyncSession,
    state: StateManager,
    state_data: dict,
    __: ShouldBeOwner,
):
    await state.upsert_context(db=db, state=PlacementGroupCreateForm.type, remark=message.text)
    update = await message.answer(
        text=Dialogs.PLACEMENT_GROUPS_SELECT_TYPE,
        reply_markup=BotKB.placement_groups_back(),
    )
    return await UserMessage.clear(update)


@router.callback_query(
    StateFilter(PlacementGroupCreateForm.type),
    BotCB.filter(area=AreaType.PLACEMENT_GROUP, task=TaskType.INFO),
)
async def type_back_handler(
    callback_query: CallbackQuery,
    db: AsyncSession,
    state: StateManager,
    __: ShouldBeOwner,
):
    await state.clear_state(db=db)
    return await callback_query.message.edit(
        text=Dialogs.PLACEMENT_GROUPS_MENU,
        reply_markup=BotKB.placement_groups_menu(placement_groups=[]),
    )


@router.callback_query(
    StateFilter(PlacementGroupCreateForm.type),
    BotCB.filter(area=AreaType.PLACEMENT_GROUP, task=TaskType.CREATE),
)
async def create_placement_group(
    callback_query: CallbackQuery,
    callback_data: BotCB,
    db: AsyncSession,
    state: StateManager,
    state_data: dict,
    hetzner: GetHetzner,
    __: ShouldBeOwner,
):
    try:
        response = await hetzner.create_placement_group(
            name=state_data["remark"],
            type="spread",
        )
    except Exception:
        return await callback_query.answer(text=Dialogs.PLACEMENT_GROUPS_CREATE_FAILED, show_alert=True)
    if not response:
        return await callback_query.answer(text=Dialogs.PLACEMENT_GROUPS_CREATE_FAILED, show_alert=True)
    await state.clear_state(db=db)
    update = await callback_query.message.edit(
        text=Dialogs.PLACEMENT_GROUPS_CREATE_SUCCESS,
        reply_markup=BotKB.placement_groups_back(id=response.placement_group.id),
    )
    return await UserMessage.add(update)
