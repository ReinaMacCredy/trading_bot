from fastapi import APIRouter, status, Depends
from typing import List
from src.web.services import OrderService
from src.web.models.orders import Order
from src.web.models.state_responses import SuccessResponse, ErrorResponse
from src.web.dependencies import get_order_service

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
    result = await order_service.create_order(order)
    return SuccessResponse(
        status="success",
        message=f"Order created for {order.symbol}",
        data={"order": result}
    )