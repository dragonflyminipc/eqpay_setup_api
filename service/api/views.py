from .responses import StartStakingResponse, StopStakingResponse, InfoResponse, UpdateResponse
from .responses import InitResponse, StartMinerResponse, StopMinerResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from .args import InitArgs, StartMinerArgs, BaseArgs
from getmac import get_mac_address as gma
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from ..decorators import request_check
from ..db import get_async_session
from ..models import Settings
from ..clients import Bitcoin
from sqlmodel import select
from ..errors import Abort
from .. import utils
import requests
import zipfile
import shutil
import config
import json
import os

router = APIRouter(prefix="/api")

@router.post(
    "/init",
    tags=["Setup"],
    summary="Set up and start up an eqpay node",
    response_model=InitResponse
)
async def init(
    body: InitArgs,
    session: AsyncSession = Depends(get_async_session)
):
    if body.mac_address.replace("-", ":") != gma().replace("-", ":"):
        raise Abort("general", "wrong-mac")

    query = await session.exec(select(Settings))

    if not (settings := query.one_or_none()):
        settings = Settings()

    session.add(settings)
    await session.commit()
    await session.refresh(settings)

    if settings.initialised:
        raise Abort("init", "already-initialised")

    latest_release = requests.get(config.github_releases_endpoint)

    if latest_release.status_code != 200:
        raise Abort("init", "no-node-files")

    response = json.loads(latest_release.text)

    version = response["tag_name"]
    files = response["assets"]

    eqpay_node_download = None

    for file in files:
        if file["name"] == "eqpay-Linux.zip":
            eqpay_node_download = file["browser_download_url"]

    if not eqpay_node_download:
        raise Abort("init", "no-node-files")

    response = requests.get(eqpay_node_download)

    with open("node.zip", 'wb') as f:
        f.write(response.content)

    with zipfile.ZipFile("node.zip") as z:
        z.extractall("node")

    if os.path.exists("node.zip"):
        os.remove("node.zip")

    # Loop through all the files of our zip and find the executable
    # Then move it to the bottom level of the folder

    node_executable_path = ""

    for subdir, dirs, files in os.walk("node/"):
        for file in files:
            filename = os.path.join(subdir, file)

            if config.node_executable in filename:
                if filename[-(len(config.node_executable)+1):] == config.node_executable:
                    os.rename(filename, f"node/{config.node_executable}")

    os.chmod(f"node/{config.node_executable}", 0o777)

    settings.node_version = version
    settings.init_timestamp = datetime.utcnow()
    settings.initialised = True
    settings.product_id = body.product_id
    settings.user_id = body.user_id
    settings.email = body.email

    await session.commit()
    await session.refresh(settings)
    
    return settings

@router.post(
    "/miner/start",
    tags=["Mining"],
    summary="Start mining",
    response_model=StartMinerResponse
)
async def start(
    body: StartMinerArgs,
    settings: Settings = Depends(request_check),
    session: AsyncSession = Depends(get_async_session)
):
    if not settings.synced:
        raise Abort("general", "not-synced")

    client = Bitcoin(config.node_endpoint)

    response = client.make_request("minerstart", [body.threads])

    if response["error"]:
        raise Abort("general", "internal-error")

    settings.threads = body.threads
    settings.mining = True

    if not settings.mining_start_timestamp:
        settings.mining_start_timestamp = datetime.utcnow()

    await session.commit()
    await session.refresh(settings)

    return {
        "mining_start_timestamp": settings.mining_start_timestamp,
        "mining": settings.mining,
        "threads": settings.threads
    }

@router.post(
    "/miner/stop",
    tags=["Mining"],
    summary="Stop mining",
    response_model=StopMinerResponse
)
async def stop(
    body: BaseArgs,
    settings: Settings = Depends(request_check),
    session: AsyncSession = Depends(get_async_session)
):
    if not settings.synced:
        raise Abort("general", "not-synced")

    client = Bitcoin(config.node_endpoint)

    response = client.make_request("minerstop", [])

    if response["error"]:
        raise Abort("general", "internal-error")

    settings.threads = 0
    settings.mining = False

    time_spent_mining = timedelta(0)

    if settings.mining_start_timestamp:
        time_spent_mining = datetime.utcnow() - settings.mining_start_timestamp

    settings.mining_start_timestamp = None

    await session.commit()
    await session.refresh(settings)

    return {
        "time_spent_mining": int(time_spent_mining.total_seconds()),
        "mining": settings.mining,
        "threads": settings.threads
    }

@router.post(
    "/staking/start",
    tags=["Staking"],
    summary="Start staking",
    response_model=StartStakingResponse
)
async def start(
    body: BaseArgs,
    settings: Settings = Depends(request_check),
    session: AsyncSession = Depends(get_async_session)
):
    if not settings.synced:
        raise Abort("general", "not-synced")

    client = Bitcoin(config.node_endpoint)

    response = client.make_request("stakerstart", [])

    if response["error"]:
        raise Abort("general", "internal-error")

    settings.staking = True

    if not settings.staking_start_timestamp:
        settings.staking_start_timestamp = datetime.utcnow()

    await session.commit()
    await session.refresh(settings)

    return {
        "staking_start_timestamp": settings.staking_start_timestamp,
        "staking": settings.staking,
    }

@router.post(
    "/staking/stop",
    tags=["Staking"],
    summary="Stop staking",
    response_model=StopStakingResponse
)
async def stop(
    body: BaseArgs,
    settings: Settings = Depends(request_check),
    session: AsyncSession = Depends(get_async_session)
):
    if not settings.synced:
        raise Abort("general", "not-synced")

    client = Bitcoin(config.node_endpoint)

    response = client.make_request("stakerstop", [])

    if response["error"]:
        raise Abort("general", "internal-error")

    settings.staking = False

    time_spent_mining = timedelta(0)

    if settings.staking_start_timestamp:
        time_spent_staking = datetime.utcnow() - settings.staking_start_timestamp

    settings.staking_start_timestamp = None

    await session.commit()
    await session.refresh(settings)

    return {
        "time_spent_staking": int(time_spent_staking.total_seconds()),
        "staking": settings.staking
    }

@router.get(
    "/info",
    tags=["Info"],
    summary="Get node and mining info",
    response_model=InfoResponse
)
async def info(
    mac_address: str,
    product_id: str,
    session: AsyncSession = Depends(get_async_session)
):
    if mac_address.replace("-", ":") != gma().replace("-", ":"):
        raise Abort("general", "wrong-mac")

    settings_query = await session.exec(select(Settings))

    if not (settings := settings_query.one_or_none()):
        settings = Settings()

    session.add(settings)
    await session.commit()
    await session.refresh(settings)

    if product_id != settings.product_id:
        raise Abort("general", "wrong-product-id")

    if not settings.initialised:
        raise Abort("general", "not-initialised")

    result = {}

    client = Bitcoin(config.node_endpoint)

    response = requests.get("https://equitypay.online/info")

    if response.status_code != 200:
        raise Abort("general", "internal-error")

    response = json.loads(response.text)

    if response["error"]:
        raise Abort("general", "internal-error")

    height = response["result"]["blocks"]

    blockchain_info = client.make_request("getblockchaininfo", [])

    if blockchain_info["error"]:
        raise Abort("general", "internal-error")

    local_height = blockchain_info["result"]["blocks"]

    result["sync"] = {
        "synced": settings.synced,
        "local_height": local_height,
        "height": height
    }

    wallet_info = client.make_request("getwalletinfo", [])

    if wallet_info["error"]:
        raise Abort("general", "internal-error")

    result["wallet"] = {
        "balance": wallet_info["result"]["balance"],
        "unconfirmed_balance": wallet_info["result"]["unconfirmed_balance"],
        "immature_balance": wallet_info["result"]["immature_balance"],
        "stake": wallet_info["result"]["stake"]
    }

    start_timestamp = None

    if settings.mining_start_timestamp and settings.staking_start_timestamp:
        start_timestamp = min(int(settings.mining_start_timestamp.timestamp()), int(settings.staking_start_timestamp.timestamp()))
    else:
        if settings.mining_start_timestamp:
            start_timestamp = int(settings.mining_start_timestamp.timestamp())
        elif settings.staking_start_timestamp:
            start_timestamp = int(settings.staking_start_timestamp.timestamp())

    coins_mined = utils.get_mined_coins(start_timestamp) if start_timestamp else 0

    result["mining"] = {
        "mining": settings.mining,
        "staking": settings.staking,
        "threads": settings.threads,
        "mining_start_timestamp": settings.mining_start_timestamp,
        "staking_start_timestamp": settings.staking_start_timestamp,
        "reward": coins_mined
    }

    return result

@router.post(
    "/update",
    tags=["Update"],
    summary="Try to update the node",
    response_model=UpdateResponse
)
async def update(
    body: BaseArgs,
    settings: Settings = Depends(request_check),
    session: AsyncSession = Depends(get_async_session)
):
    response = requests.get(config.github_releases_endpoint)

    if response.status_code != 200:
        return

    response = json.loads(response.text)

    version = response["tag_name"]
    files = response["assets"]

    result = {
        "version": version,
        "updated": False
    }

    if version != settings.node_version:
        eqpay_node_download = None

        for file in files:
            if file["name"] == "eqpay-Linux.zip":
                eqpay_node_download = file["browser_download_url"]

        if not eqpay_node_download:
            raise Abort("update", "no-node-files")

        response = requests.get(eqpay_node_download)

        if os.path.exists("node"):
            shutil.rmtree("node")

        with open("node.zip", 'wb') as f:
            f.write(response.content)

        with zipfile.ZipFile("node.zip") as z:
            z.extractall("node")

        if os.path.exists("node.zip"):
            os.remove("node.zip")

        # Loop through all the files of our zip and find the executable
        # Then move it to the bottom level of the folder

        node_executable_path = ""

        for subdir, dirs, files in os.walk("node/"):
            for file in files:
                filename = os.path.join(subdir, file)

                if config.node_executable in filename:
                    if filename[-(len(config.node_executable)+1):] == config.node_executable:
                        os.rename(filename, f"node/{config.node_executable}")

        os.chmod(f"node/{config.node_executable}", 0o777)

        utils.kill_process("eqpayd")

        settings.node_version = version

        result["updated"] = True

        await session.commit()

    return result
