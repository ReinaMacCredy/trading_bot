async def process_order(order):
    print("[LỆNH NHẬN]", order)

    return {
        "status": "success",
        "message": f"Lệnh {order.name} ({'MUA' if order.action else 'BÁN'}) {order.symbol} đã nhận",
        "data": order.dict()
    }
