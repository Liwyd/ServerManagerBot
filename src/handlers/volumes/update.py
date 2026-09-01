from eiogram import Router
from eiogram.filters import StateFilter, Text
from eiogram.state import State, StateGroup, StateManager
from eiogram.types import CallbackQuery, Message

from src.db import AsyncSession
from src.keys import AreaType, BotCB, BotKB, StepType, TaskType
from src.lang import Dialogs
from src.utils.depends import GetHetzner, ShouldBeOwner

router = Router()


class VolumeUpdateForm(StateGroup):
    approval = State()
    input = State()
    select = State()


@router.callback_query(BotCB.filter(area=AreaType.VOLUME, task=TaskType.UPDATE))
async def volumes_update(
    callback_query: CallbackQuery,
    callback_data: BotCB,
    db: AsyncSession,
    state: StateManager,
    hetzner: GetHetzner,
    __: ShouldBeOwner,
):
    kb = BotKB.volumes_back(id=callback_data.target)
    volume = await hetzner.get_volume_by_id(int(callback_data.target))
    if not volume:
        return await callback_query.message.edit(text=Dialogs.VOLUMES_NOT_FOUND, reply_markup=kb)
    match callback_data.step:
        case StepType.VOLUMES_DELETE:
            text = Dialogs.ACTIONS_CONFIRM
            _state = VolumeUpdateForm.approval
            kb = BotKB.approval(area=AreaType.VOLUME, task=TaskType.UPDATE)
        case StepType.VOLUMES_REMARK:
            text = Dialogs.VOLUMES_ENTER_REMARK
            _state = VolumeUpdateForm.input
        case StepType.VOLUMES_RESIZE:
            text = Dialogs.VOLUMES_ENTER_SIZE
            _state = VolumeUpdateForm.input
        case StepType.VOLUMES_ATTACH:
            servers = await hetzner.get_servers()
            if not servers:
                return await callback_query.answer(text=Dialogs.VOLUMES_NOT_FOUND, show_alert=True)
            text = Dialogs.VOLUMES_SELECT_SERVER
            _state = VolumeUpdateForm.select
            kb = BotKB.volumes_select_server(servers=servers)
        case StepType.VOLUMES_DETACH:
            text = Dialogs.ACTIONS_CONFIRM
            _state = VolumeUpdateForm.approval
            kb = BotKB.approval(area=AreaType.VOLUME, task=TaskType.UPDATE)
        case _:
            return await callback_query.answer(text="Invalid step!", show_alert=True)
    await state.upsert_context(db=db, state=_state, step=callback_data.step, target=callback_data.target)
    return await callback_query.message.edit(text=text, reply_markup=kb)


@router.message(StateFilter(VolumeUpdateForm.input), Text())
async def input_handler(
    message: Message,
    db: AsyncSession,
    state: StateManager,
    hetzner: GetHetzner,
    state_data: dict,
    __: ShouldBeOwner,
):
    volume = await hetzner.get_volume_by_id(int(state_data["target"]))
    if not volume:
        return await message.answer(text=Dialogs.VOLUMES_NOT_FOUND)

    match state_data["step"]:
        case StepType.VOLUMES_REMARK:
            await hetzner.update_volume(volume, name=message.text)
        case StepType.VOLUMES_RESIZE:
            try:
                size = int(message.text)
                if size < 10:
                    raise ValueError
            except ValueError:
                return await message.answer(text=Dialogs.VOLUMES_ENTER_SIZE, reply_markup=BotKB.volumes_back(id=volume.id))
            await hetzner.resize_volume(volume, size=size)
        case _:
            return await message.answer(text="Invalid step!", reply_markup=BotKB.volumes_back(id=volume.id))

    await state.clear_state(db=db)
    return await message.answer(text=Dialogs.VOLUMES_UPDATE_SUCCESS, reply_markup=BotKB.volumes_back(id=volume.id))


@router.callback_query(StateFilter(VolumeUpdateForm.approval), BotCB.filter(area=AreaType.VOLUME, task=TaskType.UPDATE))
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
        return await callback_query.message.edit(text=Dialogs.ACTIONS_CANCELLED, reply_markup=BotKB.volumes_back())

    volume = await hetzner.get_volume_by_id(int(state_data["target"]))
    if not volume:
        return await callback_query.answer(text=Dialogs.VOLUMES_NOT_FOUND, show_alert=True)

    kb = BotKB.volumes_back(id=volume.id)
    match state_data["step"]:
        case StepType.VOLUMES_DELETE:
            await hetzner.delete_volume(volume)
            kb = BotKB.volumes_back()
        case StepType.VOLUMES_DETACH:
            await callback_query.message.edit(text=Dialogs.ACTIONS_WAITING)
            await hetzner.detach_volume(volume)

    await state.clear_state(db=db)
    return await callback_query.message.edit(text=Dialogs.VOLUMES_UPDATE_SUCCESS, reply_markup=kb)


@router.callback_query(StateFilter(VolumeUpdateForm.select), BotCB.filter(area=AreaType.VOLUME, task=TaskType.UPDATE))
async def select_handler(
    callback_query: CallbackQuery,
    callback_data: BotCB,
    db: AsyncSession,
    state: StateManager,
    hetzner: GetHetzner,
    state_data: dict,
    __: ShouldBeOwner,
):
    volume = await hetzner.get_volume_by_id(int(state_data["target"]))
    if not volume:
        return await callback_query.answer(text=Dialogs.VOLUMES_NOT_FOUND, show_alert=True)

    server = await hetzner.get_server_by_id(int(callback_data.target))
    if not server:
        return await callback_query.answer(text=Dialogs.VOLUMES_NOT_FOUND, show_alert=True)

    await hetzner.attach_volume(volume, server=server)

    await state.clear_state(db=db)
    return await callback_query.message.edit(text=Dialogs.VOLUMES_UPDATE_SUCCESS, reply_markup=BotKB.volumes_back(id=volume.id))
