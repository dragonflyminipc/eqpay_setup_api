from sqlmodel.ext.asyncio.session import AsyncSession
from getmac import get_mac_address as gma
from service.api.args import BaseArgs
from .db import get_async_session
from fastapi import Depends, Body
from .models import Settings
from sqlmodel import select
from .errors import Abort

async def request_check(
    body: BaseArgs,
    session: AsyncSession = Depends(get_async_session),
) -> Settings:
    if body.mac_address.replace("-", ":") != gma().replace("-", ":"):
        raise Abort("general", "wrong-mac")

    query = await session.exec(select(Settings))

    if not (settings := query.one_or_none()):
        settings = Settings()

    session.add(settings)
    await session.commit()
    await session.refresh(settings)

    if body.product_id != settings.product_id:
        raise Abort("general", "wrong-product-id")

    if not settings.initialised:
        raise Abort("general", "not-initialised")

    return settings
