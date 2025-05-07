import os
from fastapi import FastAPI, HTTPException
import httpx


# Initialize FastAPI constructor
app = FastAPI()
# Initialize endpoint URL
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


def main():
    print("Hello from timechain-backend!")

@app.get("/")
async def root():
    return {"message": "Hello World!"}

@app.get("/fee-estimate")
async def fee_estimate(blocks: int=1):
    """
    Estimate fee to confirm in `blocks` number of blocks,
    returning sats/vByte instead of BTC/vkB.
    """
    if blocks > 1008:
        raise HTTPException(status_code=502, detail="Max target block value is 1008. Please use a smaller target block value")
    
    result : dict = await call_rpc("estimatesmartfee", [blocks])
    feerate_btc_per_kb : float = result.get("feerate")
    if feerate_btc_per_kb is None:
        # Response has "feerate": null 
        raise HTTPException(status_code=404,
                            detail=f"No fee estimate available for {blocks} blocks")
    
    #Convert BTC/vKByte to sats/vbyte
    feerate_sats_per_vbyte : float = feerate_btc_per_kb * 100_000 # 1 btc = 100_000_000 sats and 1 kb = 1000 bytes

    return {
        "target_blocks" : result.get("blocks"),
        "estimated_fee_BTC/vkB": feerate_btc_per_kb,
        "estimated_fee_sats/vB": round(feerate_sats_per_vbyte)
    }

if __name__ == "__main__":
    main()
