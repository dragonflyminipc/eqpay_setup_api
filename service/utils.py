from pydantic.datetime_parse import parse_datetime
from service.clients import Bitcoin
from datetime import datetime
import requests
import config
import signal
import json
import os

class Datetime(int):
    @classmethod
    def __get_validators__(cls):
        yield parse_datetime
        yield cls.validate

    @classmethod
    def validate(cls, value) -> int:
        return int(value.timestamp())

def ping_rpc():
    client = Bitcoin(config.node_endpoint)
    response = client.make_request("getblockchaininfo", [])

    return response["error"] is None

def get_peers():
    url = "https://equitypay.online/data/peers"
    peers = []

    response = requests.get(url)

    if response.status_code != 200:
        return []

    response = json.loads(response.text)

    if response["error"]:
        return []

    datetime_format = "%a, %d %b %Y %H:%M:%S %Z"

    for peer in response["result"]:
        dt_object = datetime.strptime(peer["last"], datetime_format)
        delta = datetime.utcnow() - dt_object

        if delta.days >= 1:
            continue

        peers.append(peer)

    return peers

def get_mined_coins(after_timestamp):
    coins = 0

    client = Bitcoin(config.node_endpoint)

    response = client.make_request("listtransactions", ["*", 10000])

    for tx in response["result"]:
        if tx["generated"] != True:
            continue

        if tx["category"] == "orphan":
            continue

        if "blocktime" in tx and tx["blocktime"] < after_timestamp:
            continue

        coins += tx["amount"]

    return round(coins, 8)

def kill_process(name):
    for line in os.popen(f"ps ax | grep {name} | grep -v grep"):
        fields = line.split()
         
        # extracting Process ID from the output
        pid = fields[0]
         
        # terminating process
        os.kill(int(pid), signal.SIGKILL)
