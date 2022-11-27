from fastapi import Body, Query
from pydantic import BaseModel

class InitArgs(BaseModel):
    mac_address: str
    product_id: str
    user_id: str
    email: str

class BaseArgs(BaseModel):
    mac_address: str
    product_id: str

class StartMinerArgs(BaseArgs):
    threads: int = Body(default=32, le=1024, ge=1)
