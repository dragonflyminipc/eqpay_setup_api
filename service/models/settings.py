from datetime import datetime
from .base import BaseTable
from typing import Union

class Settings(BaseTable, table=True):
    __tablename__ = "service_settings"

    node_version: str = "0.0.0"

    mining_start_timestamp: Union[datetime, None] = None
    staking_start_timestamp: Union[datetime, None] = None
    init_timestamp: Union[datetime, None] = None

    initialised: bool = False
    added_peers: bool = False
    synced: bool = False
    mining: bool = False
    staking: bool = False

    threads: int = 0

    product_id: Union[str, None] = None
    user_id: Union[str, None] = None
    email: Union[str, None] = None
