from fastapi import APIRouter, status, Depends
from typing import List
from src.web.services import OrderService
from src.web.api.models import Order, SuccessResponse, ErrorResponse
from src.web.api.dependencies import get_order_service

router = APIRouter(prefix="/orders", tags=["orders"])

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse,
    responses={
        201: {"model": SuccessResponse},
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Create order",
    description="Create a new pending order",
    response_description="Order creation result"
)
async def create_order(
    order: Order,
    order_service: OrderService = Depends(get_order_service)
):
    """Create a new order"""
    result = await order_service.create_order(order.dict())
    return SuccessResponse(
        message=f"Order created for {order.symbol}",
        data={"order": result}
    )

@router.get(
    "/{symbol}",
    status_code=status.HTTP_200_OK,
    response_model=SuccessResponse,
    responses={
        200: {"model": SuccessResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Get orders",
    description="Get all pending orders for a symbol",
    response_description="List of pending orders"
)
async def get_orders(
    symbol: str,
    order_service: OrderService = Depends(get_order_service)
):
    """Get all pending orders for a symbol"""
    orders = await order_service.get_orders(symbol)
    return SuccessResponse(
        message=f"Retrieved orders for {symbol}",
        data={"orders": orders}
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
    summary="Cancel orders",
    description="Cancel all pending orders for a symbol",
    response_description="Order cancellation result"
)
async def cancel_orders(
    symbol: str,
    order_service: OrderService = Depends(get_order_service)
):
    """Cancel all pending orders for a symbol"""
    await order_service.cancel_orders(symbol)
    return SuccessResponse(
        message=f"Cancelled all orders for {symbol}"
    ) 