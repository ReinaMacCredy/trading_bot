from fastapi import APIRouter, status, Depends
from src.web.models.signals import TradingViewSignal
from archi import Broker, Emitter
from src.web.dependencies import get_trading_view_emitter, get_trading_view_emitter_2
from src.web.models.state_responses import SuccessResponse, ErrorResponse

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
    emitter: Emitter = Depends(get_trading_view_emitter)
):
    """Process TradingView webhook signal"""
    try:
        await emitter.emit()
    
        return SuccessResponse(
            status="success",
            message=f"Signal processed for {signal.symbol}",
            data={"signal": signal.dict()}
        )
    except Exception as e:
        return ErrorResponse(
            status="error",
            message=f"Failed to process signal: {e}",
            details={"signal": signal.dict()}
        )

######################################

@router.post(
    "/tradingview_2",
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
async def handle_tradingview_webhook_2(
    signal: TradingViewSignal,
    emitter: Emitter = Depends(get_trading_view_emitter_2)
):
    """Process TradingView webhook signal"""
    try:
        await emitter.emit()
    
        return SuccessResponse(
            status="success",
            message=f"Signal processed for {signal.symbol}",
            data={"signal": signal.dict()}
        )
    except Exception as e:
        return ErrorResponse(
            status="error",
            message=f"Failed to process signal: {e}",
            details={"signal": signal.dict()}
        )