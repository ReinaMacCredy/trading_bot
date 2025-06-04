from dataclasses import dataclass
from datetime import datetime
from typing import List

@dataclass
class OrderRecord:
    order_id: str
    symbol: str
    side: str
    amount: float
    price: float
    timestamp: datetime
    status: str
    order_type: str

class OrderHistory:
    """In-memory order history storage"""

    def __init__(self) -> None:
        self.orders: List[OrderRecord] = []

    def add_order(self, order_id: str, symbol: str, side: str, amount: float, price: float, status: str, order_type: str) -> None:
        record = OrderRecord(
            order_id=order_id,
            symbol=symbol,
            side=side,
            amount=amount,
            price=price,
            timestamp=datetime.now(),
            status=status,
            order_type=order_type,
        )
        self.orders.append(record)

    def get_all_orders(self) -> List[OrderRecord]:
        return list(self.orders)

    def get_last_orders(self, limit: int = 10) -> List[OrderRecord]:
        return self.orders[-limit:]
