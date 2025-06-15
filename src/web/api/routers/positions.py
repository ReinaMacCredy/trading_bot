from fastapi import APIRouter, status, Depends
from typing import List
from src.web.services import PositionService
from src.web.api.models import Position, PositionUpdate, SuccessResponse, ErrorResponse, PositionsResponse
from src.web.api.dependencies import get_position_service

router = APIRouter(prefix="/positions", tags=["positions"])

@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=PositionsResponse,
    responses={
        200: {"model": PositionsResponse},
        500: {"model": ErrorResponse}
    },
    summary="Get all positions",
    description="Get all active trading positions",
    response_description="List of active positions"
)
async def get_positions(
    position_service: PositionService = Depends(get_position_service)
):
    """Get all active positions"""
    positions = await position_service.get_positions()
    return PositionsResponse(
        status="success",
        message="Retrieved all positions",
        positions=positions
    )

@router.put(
    "/{symbol}",
    status_code=status.HTTP_200_OK,
    response_model=SuccessResponse,
    responses={
        200: {"model": SuccessResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Update position",
    description="""
    Update take profit or stop loss for a position.
    
    At least one of take_profit or stop_loss must be provided.
    """,
    response_description="Position update result"
)
async def update_position(
    symbol: str,
    update: PositionUpdate,
    position_service: PositionService = Depends(get_position_service)
):
    """Update take profit or stop loss for a position"""
    await position_service.update_position(
        symbol,
        update.take_profit,
        update.stop_loss
    )
    return SuccessResponse(
        status="success",
        message=f"Updated position for {symbol}",
        data=update.dict()
    )

@router.delete(
    "/{symbol}",
    status_code=status.HTTP_200_OK,
    response_model=SuccessResponse,
    responses={
        200: {"model": SuccessResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Close position",
    description="Close an active trading position",
    response_description="Position close result"
)
async def close_position(
    symbol: str,
    position_service: PositionService = Depends(get_position_service)
):
    """Close a position"""
    await position_service.close_position(symbol)
    return SuccessResponse(
        status="success",
        message=f"Closed position for {symbol}"
    ) 