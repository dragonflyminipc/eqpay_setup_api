from sqlmodel.ext.asyncio.session import AsyncSession
from service.db import async_engine
from service.models import Settings
from service.clients import Bitcoin
from sqlmodel import select
from .. import utils
import requests
import config
import json
import time

eqpay_chaininfo_api = "https://equitypay.online/info"

async def check_sync():
    async with AsyncSession(async_engine) as session:
        settings_query = await session.exec(select(Settings))

        if not (settings := settings_query.one_or_none()):
            return

        session.add(settings)
        await session.refresh(settings)

        # Haven't initialised the node yet
        if not settings.initialised:
            return

        client = Bitcoin(config.node_endpoint)

        # Node doesn't respond
        if not utils.ping_rpc():
            return

        response = requests.get(eqpay_chaininfo_api)

        if response.status_code != 200:
            return

        response = json.loads(response.text)

        if response["error"]:
            return

        height = response["result"]["blocks"]

        response = client.make_request("getblockchaininfo", [])

        if response["error"]:
            return

        local_height = response["result"]["blocks"]

        if local_height == height and not settings.synced:
            settings.synced = True

            time_str = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.localtime())

            print(f"[{time_str}] Updated the synced status {local_height}/{height} blocks")

            await session.commit()
