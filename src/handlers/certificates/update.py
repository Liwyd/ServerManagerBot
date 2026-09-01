from eiogram import Router
from eiogram.filters import StateFilter, Text
from eiogram.state import State, StateGroup, StateManager
from eiogram.types import CallbackQuery, Message

from src.db import AsyncSession
from src.keys import AreaType, BotCB, BotKB, StepType, TaskType
from src.lang import Dialogs
from src.utils.depends import GetHetzner, ShouldBeOwner

router = Router()


class CertificateUpdateForm(StateGroup):
    approval = State()
    input = State()


@router.callback_query(BotCB.filter(area=AreaType.CERTIFICATE, task=TaskType.UPDATE))
async def certificates_update(
    callback_query: CallbackQuery,
    callback_data: BotCB,
    db: AsyncSession,
    state: StateManager,
    hetzner: GetHetzner,
    __: ShouldBeOwner,
):
    kb = BotKB.certificates_back(id=callback_data.target)
    certificate = await hetzner.get_certificate_by_id(int(callback_data.target))
    if not certificate:
        return await callback_query.message.edit(text=Dialogs.CERTIFICATES_NOT_FOUND, reply_markup=kb)
    match callback_data.step:
        case StepType.CERTIFICATES_DELETE:
            text = Dialogs.ACTIONS_CONFIRM
            _state = CertificateUpdateForm.approval
            kb = BotKB.approval(area=AreaType.CERTIFICATE, task=TaskType.UPDATE)
        case StepType.CERTIFICATES_REMARK:
            text = Dialogs.CERTIFICATES_ENTER_REMARK
            _state = CertificateUpdateForm.input
        case _:
            return await callback_query.answer(text="Invalid step!", show_alert=True)
    await state.upsert_context(db=db, state=_state, step=callback_data.step, target=callback_data.target)
    return await callback_query.message.edit(text=text, reply_markup=kb)


@router.message(StateFilter(CertificateUpdateForm.input), Text())
async def input_handler(
    message: Message,
    db: AsyncSession,
    state: StateManager,
    hetzner: GetHetzner,
    state_data: dict,
    __: ShouldBeOwner,
):
    certificate = await hetzner.get_certificate_by_id(int(state_data["target"]))
    if not certificate:
        return await message.answer(text=Dialogs.CERTIFICATES_NOT_FOUND)

    match state_data["step"]:
        case StepType.CERTIFICATES_REMARK:
            await hetzner.update_certificate(certificate, name=message.text)
        case _:
            return await message.answer(text="Invalid step!", reply_markup=BotKB.certificates_back(id=certificate.id))

    await state.clear_state(db=db)
    return await message.answer(
        text=Dialogs.CERTIFICATES_UPDATE_SUCCESS, reply_markup=BotKB.certificates_back(id=certificate.id)
    )


@router.callback_query(
    StateFilter(CertificateUpdateForm.approval), BotCB.filter(area=AreaType.CERTIFICATE, task=TaskType.UPDATE)
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
        return await callback_query.message.edit(text=Dialogs.ACTIONS_CANCELLED, reply_markup=BotKB.certificates_back())

    certificate = await hetzner.get_certificate_by_id(int(state_data["target"]))
    if not certificate:
        return await callback_query.answer(text=Dialogs.CERTIFICATES_NOT_FOUND, show_alert=True)

    kb = BotKB.certificates_back(id=certificate.id)
    match state_data["step"]:
        case StepType.CERTIFICATES_DELETE:
            await hetzner.delete_certificate(certificate)
            kb = BotKB.certificates_back()

    await state.clear_state(db=db)
    return await callback_query.message.edit(text=Dialogs.CERTIFICATES_UPDATE_SUCCESS, reply_markup=kb)
