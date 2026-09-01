import logging
from typing import Annotated

from eiogram.state import StateManager
from eiogram.types import Update
from eiogram.utils.depends import Depends

from src.db import AsyncSession, Client, User, UserMessage
from src.utils.async_hetzner import AsyncHetznerClient


async def clear_state(db: AsyncSession, state: StateManager) -> None:
    await state.clear_state(db=db)


async def get_hetzner(db: AsyncSession, state_data: dict) -> AsyncHetznerClient:
    client_id = state_data.get("client_id")
    if client_id is None:
        logging.warning("No client_id found in state data.")
        raise Exception("No client selected")
    client = await Client.get_by_id(db, client_id)
    if not client:
        logging.warning(f"Client not found for client_id: {client_id}")
        raise Exception("Client not found")
    return AsyncHetznerClient(token=client.secret)


async def should_be_owner(update: Update, dbuser: User, db: AsyncSession) -> None:
    if not dbuser.is_owner:
        if update.callback_query:
            await update.callback_query.answer("Access Denied", show_alert=True)
        elif update.message:
            _update = await update.message.answer("Access Denied", reply_markup=None)
            await UserMessage.clear(_update)
        raise Exception("Access Denied")


GetHetzner = Annotated[AsyncHetznerClient, Depends(get_hetzner)]
ClearState = Annotated[None, Depends(clear_state)]
ShouldBeOwner = Annotated[None, Depends(should_be_owner)]
