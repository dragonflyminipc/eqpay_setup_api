from pydantic import BaseModel, Field
from ..utils import Datetime
from typing import Union

class InitResponse(BaseModel):
    init_timestamp: Datetime = Field(example=1659766201)
    initialised: bool = Field(example=True)
    product_id: str = Field(example="some product id")
    user_id: str = Field(example="some user id")
    email: str = Field(example="example@gmail.com")

    class Config:
        orm_mode = True

class StartMinerResponse(BaseModel):
    mining_start_timestamp: Datetime = Field(example=1659766201)
    mining: bool = Field(example=True)
    threads: int = Field(example=32)

class StopMinerResponse(BaseModel):
    time_spent_mining: int = Field(example=70)
    mining: bool = Field(example=False)
    threads: int = Field(example=0)

class StartStakingResponse(BaseModel):
    staking_start_timestamp: Datetime = Field(example=1659766201)
    staking: bool = Field(example=True)

class StopStakingResponse(BaseModel):
    time_spent_staking: int = Field(example=70)
    staking: bool = Field(example=False)

class InfoSyncResponse(BaseModel):
    synced: bool = Field(example=True)
    local_height: int = Field(example=30000)
    height: int = Field(example=30000)

class InfoWalletResponse(BaseModel):
    balance: float = Field(example=12.04)
    unconfirmed_balance: float = Field(example=0)
    immature_balance: float = Field(example=3.08)
    stake: float = Field(example=2.0)

class InfoMiningResponse(BaseModel):
    mining: bool = Field(example=True)
    staking: bool = Field(example=False)
    threads: int = Field(example=32)
    reward: float = Field(example=3.08)
    mining_start_timestamp: Union[Datetime, None] = Field(example=1659766201)
    staking_start_timestamp: Union[Datetime, None] = Field(example=1659766201)

class InfoResponse(BaseModel):
    sync: InfoSyncResponse
    wallet: InfoWalletResponse
    mining: InfoMiningResponse

class UpdateResponse(BaseModel):
    updated: bool = Field(example=True)
    version: str = Field(example="1.0.0")
