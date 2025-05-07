from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from ..clients.client import call_rpc, get_input_total, get_output_total

router = APIRouter()

logger = logging.getLogger()


class GetTxFeesResponseModel(BaseModel):
    txid:       str
    input_btc:  float
    output_btc: float
    fees:       int

class FeeEstimateResponseModel(BaseModel):
    target_blocks:  int
    estimated_fee_BTC_per_kvB: float
    estimated_fee_sats_per_vB: int

@router.get("/fee-estimate", response_model=FeeEstimateResponseModel)
async def fee_estimate(blocks: int=1) -> FeeEstimateResponseModel:
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

    return FeeEstimateResponseModel(
        target_blocks = result.get("blocks"),
        estimated_fee_BTC_per_kvB =  feerate_btc_per_kb,
        estimated_fee_sats_per_vB = round(feerate_sats_per_vbyte)
    )


@router.get("/get-tx-fees/{txid}", response_model=GetTxFeesResponseModel)
async def get_tx_fees(txid: str) -> GetTxFeesResponseModel:
    """
    Get Transaction Fees from {txid}
    """

    try:
        result : dict = await call_rpc("getrawtransaction", [txid, True])
    except Exception as e:
        logger.exception(e)

    vin_list : list = result.get("vin")
    vout_list: list = result.get("vout")

    vin_total_btc : float = await get_input_total(vin_list)
    vout_total_btc : float = get_output_total(vout_list)

    tx_fees : float = vin_total_btc - vout_total_btc

    tx_fees_sats : int = int(tx_fees * 100_000_000)

    return GetTxFeesResponseModel(
        txid =txid,
        input_btc =  vin_total_btc,
        output_btc = vout_total_btc,
        fees =       tx_fees_sats
    )

    
    
    
