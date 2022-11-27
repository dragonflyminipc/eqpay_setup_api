from sqlmodel.ext.asyncio.session import AsyncSession
from service.db import async_engine
from service.models import Settings
from sqlmodel import select
import subprocess
import config
import shlex
import time

process = None

async def start_node():
    global process

    async with AsyncSession(async_engine) as session:
        settings_query = await session.exec(select(Settings))

        if not (settings := settings_query.one_or_none()):
            return

        session.add(settings)
        await session.refresh(settings)

        # Haven't initialised the node yet
        if not settings.initialised:
            return

        time_str = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.localtime())

        # First run, process doesn't exist yet
        if not process:
            print(f"[{time_str}] First run. Starting the process")
            process = subprocess.Popen(shlex.split(config.run_node_command))
            return

        # Our process is still running
        if process.poll() is None:
            return
        
        # Our process closed so we run it again
        print(f"[{time_str}] Process terminated, restarting")
        process = subprocess.Popen(shlex.split(config.run_node_command))
