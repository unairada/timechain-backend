import os
from typing import Any
import httpx
from fastapi import HTTPException
import logging

logger = logging.getLogger()

BLAST_RPC_URL = os.getenv("BLAST_RPC_URL", "https://bitcoin-mainnet.public.blastapi.io")

async def call_rpc(method: str, params: list = []):
    payload = {
        "jsonrpc": "1.0",
        "id": "timechain",
        "method": method,
        "params": params
    }
    async with httpx.AsyncClient() as client: # AsyncClient uses asyncio in the background to avoid blocking other incoming fastAPI requests
        resp = await client.post(BLAST_RPC_URL, json=payload) 
        # resp.raise_for_status() # raise error if 400 of 500 HTTP status
        data = resp.json()
        if data.get("error"):
            raise HTTPException(status_code=502, detail=data["error"])
        return data["result"]
    


async def get_input_total(vin_list: list[dict[str, Any]]) -> float:
    total_input : float = 0.0

    for vin in vin_list:
        txid : str = vin.get("txid")
        vout_index : int = vin.get("vout")

        try:
            result : dict = await call_rpc("getrawtransaction", [txid, True])
        except Exception as e:
            logger.exception(e)

        vout : dict = result.get("vout")[vout_index]
        vout_value : float = vout.get("value")
        
        total_input += vout_value


    return total_input

def get_output_total(vout_list : list[dict[str,Any]]) -> float:
    total_output : float = 0.0

    for vout in vout_list:
        
        vout_value : float = vout.get("value")
        total_output  += vout_value

    return total_output