from fastapi import APIRouter, status, Depends
from src.web.services import TradeExecutor
from src.web.api.models import TradingViewSignal, SuccessResponse, ErrorResponse
from src.web.api.dependencies import get_trade_executor

router = APIRouter(prefix="/webhook", tags=["webhook"])

@router.post(
    "/tradingview",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse,
    responses={
        201: {"model": SuccessResponse},
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Handle TradingView webhook",
    description="""
    Process incoming signals from TradingView.
    
    The webhook expects a JSON payload with the following structure:
    ```json
    {
        "symbol": "BTCUSDT",
        "side": "buy",
        "type": "market",
        "volume": 0.1,
        "price": null,
        "stop_loss": 49000.0,
        "take_profit": 52000.0
    }
    ```
    """,
    response_description="Signal processing result"
)
async def handle_tradingview_webhook(
    signal: TradingViewSignal,
    trade_executor: TradeExecutor = Depends(get_trade_executor)
):
    """Process TradingView webhook signal"""
    await trade_executor.process_signal(signal.dict())
    return SuccessResponse(
        status="success",
        message=f"Signal processed for {signal.symbol}",
        data={"signal": signal.dict()}
    ) 