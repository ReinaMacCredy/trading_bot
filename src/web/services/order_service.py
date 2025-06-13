# src/services/order_service.py
# ------------------------------------------
# Dịch vụ xử lý khi nhận lệnh
# Có thể mở rộng để: lưu DB, gửi Telegram/Discord...
# ------------------------------------------

async def process_order(lenh):
    print("[LỆNH NHẬN]", lenh)

    return {
        "status": "success",
        "message": f"Lệnh {lenh.ten} ({'MUA' if lenh.hanhDong else 'BÁN'}) {lenh.symbol} đã nhận",
        "data": lenh.dict()
    }
