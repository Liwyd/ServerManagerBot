from eiogram import Router
from eiogram.filters import StateFilter, Text
from eiogram.state import State, StateGroup, StateManager
from eiogram.types import CallbackQuery, Message

from src.db import AsyncSession, UserMessage
from src.keys import AreaType, BotCB, BotKB, TaskType
from src.lang import Dialogs
from src.utils.depends import GetHetzner, ShouldBeOwner

router = Router()


class CertificateCreateForm(StateGroup):
    type_select = State()
    name = State()
    certificate = State()
    private_key = State()
    domains = State()


@router.callback_query(BotCB.filter(area=AreaType.CERTIFICATE, task=TaskType.CREATE))
async def certificates_create(
    callback_query: CallbackQuery, callback_data: BotCB, db: AsyncSession, state: StateManager, __: ShouldBeOwner
):
    cert_type = callback_data.target
    if cert_type not in ("uploaded", "managed"):
        return await callback_query.answer(text=Dialogs.ACTIONS_FAILED, show_alert=True)
    await state.upsert_context(db=db, state=CertificateCreateForm.name, cert_type=cert_type)
    return await callback_query.message.edit(text=Dialogs.CERTIFICATES_ENTER_REMARK, reply_markup=BotKB.certificates_back())


@router.message(StateFilter(CertificateCreateForm.name), Text())
async def name_handler(message: Message, db: AsyncSession, state: StateManager, state_data: dict, __: ShouldBeOwner):
    cert_type = state_data["cert_type"]
    if cert_type == "uploaded":
        await state.upsert_context(db=db, state=CertificateCreateForm.certificate, name=message.text)
        update = await message.answer(text=Dialogs.CERTIFICATES_ENTER_CERT, reply_markup=BotKB.certificates_back())
    else:
        await state.upsert_context(db=db, state=CertificateCreateForm.domains, name=message.text)
        update = await message.answer(text=Dialogs.CERTIFICATES_ENTER_DOMAINS, reply_markup=BotKB.certificates_back())
    return await UserMessage.clear(update)


@router.message(StateFilter(CertificateCreateForm.certificate), Text())
async def certificate_handler(message: Message, db: AsyncSession, state: StateManager, state_data: dict, __: ShouldBeOwner):
    await state.upsert_context(db=db, state=CertificateCreateForm.private_key, certificate=message.text)
    update = await message.answer(text=Dialogs.CERTIFICATES_ENTER_KEY, reply_markup=BotKB.certificates_back())
    return await UserMessage.clear(update)


@router.message(StateFilter(CertificateCreateForm.private_key), Text())
async def private_key_handler(
    message: Message,
    db: AsyncSession,
    state: StateManager,
    hetzner: GetHetzner,
    state_data: dict,
    __: ShouldBeOwner,
):
    try:
        response = await hetzner.create_certificate(
            name=state_data["name"],
            certificate=state_data["certificate"],
            private_key=message.text,
        )
    except Exception:
        return await message.answer(text=Dialogs.CERTIFICATES_CREATE_FAILED)
    if not response:
        return await message.answer(text=Dialogs.CERTIFICATES_CREATE_FAILED)
    await state.clear_state(db=db)
    return await message.answer(text=Dialogs.CERTIFICATES_CREATE_SUCCESS, reply_markup=BotKB.certificates_back(id=response.id))


@router.message(StateFilter(CertificateCreateForm.domains), Text())
async def domains_handler(
    message: Message,
    db: AsyncSession,
    state: StateManager,
    hetzner: GetHetzner,
    state_data: dict,
    __: ShouldBeOwner,
):
    domain_names = [d.strip() for d in message.text.split(",") if d.strip()]
    if not domain_names:
        return await message.answer(text=Dialogs.CERTIFICATES_CREATE_FAILED)
    try:
        response = await hetzner.create_managed_certificate(
            name=state_data["name"],
            domain_names=domain_names,
        )
    except Exception:
        return await message.answer(text=Dialogs.CERTIFICATES_CREATE_FAILED)
    if not response:
        return await message.answer(text=Dialogs.CERTIFICATES_CREATE_FAILED)
    await state.clear_state(db=db)
    return await message.answer(
        text=Dialogs.CERTIFICATES_CREATE_SUCCESS, reply_markup=BotKB.certificates_back(id=response.certificate.id)
    )
