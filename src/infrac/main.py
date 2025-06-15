from fastapi import FastAPI, Request
import redis
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import requests

app = FastAPI()

# Kết nối Redis
try:
    r = redis.Redis(host='127.0.0.1', port=6379, decode_responses=True)
    print("🔗 Kết nối Redis:", r.ping())
except Exception as e:
    print("❌ Redis lỗi:", e)
    r = None

# Cấu hình Discord Webhook
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1383735072129159168/fgE-jfxMVWFil5SFOV1AWzv9lEm9X01Xj-NSE9KlxmrPmuG4Kl9Mbh_kM3iO4SJ0bjMS"

def send_discord_alert(message: str):
    payload = {
        "content": message
    }
    headers = {
        "Content-Type": "application/json"
    }   
    try:
        res = requests.post(DISCORD_WEBHOOK_URL, json=payload, headers=headers, timeout=5)
        if res.status_code >= 400:
            print(f"⚠️ Lỗi gửi Discord: {res.status_code} - {res.text}")
    except Exception as e:
        print("⚠️ Lỗi gửi Discord:", e)

@app.post("/webhook")
async def tradingview_webhook(req: Request):
    if r is None:
        return {"status": "error", "detail": "Redis chưa sẵn sàng."}

    try:
        data = await req.json()
        print("📩 Nhận dữ liệu từ TradingView:", data)

        # Lấy thông tin từ TradingView
        symbol = data.get("symbol", "UNKNOWN")
        price = str(data.get("price", "0"))
        signal = data.get("signal", "none")

        # ⏰ Thời gian từ TradingView
        alert_time_str = data.get("time")
        if alert_time_str:
            tv_time = datetime.fromisoformat(alert_time_str.replace("Z", "+00:00"))  # UTC
            tv_time_vn = tv_time.astimezone(ZoneInfo("Asia/Ho_Chi_Minh"))
        else:
            tv_time_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))

        received_time_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))

        # Lưu vào Redis hash
        key = f"price:{symbol}"
        r.hset(key, mapping={
            "price": price,
            "time": received_time_vn.isoformat(),
            "signal": signal
        })

        # Đẩy vào Redis Stream
        stream_key = "stream:prices"
        r.xadd(stream_key, {
            "symbol": symbol,
            "price": price,
            "signal": signal,
            "time": received_time_vn.isoformat()
        }, maxlen=1000, approximate=True)

        # Gửi thông báo Discord
        send_discord_alert(
            "-----------------------------------------------------------------------\n"
            f"🚨 Tín hiệu `{signal.upper()}` cho `{symbol}` tại giá **{price}**\n"
            f"🕰️ Nến đóng lúc: `{tv_time_vn.strftime('%H:%M:%S %d-%m-%Y')}`\n"
            f"📥 Nhận webhook lúc: `{received_time_vn.strftime('%H:%M:%S %d-%m-%Y')}`"
        )

        print(f"✅ Đã lưu {key} và đẩy vào stream {stream_key}")
        return {"status": "ok", "symbol": symbol, "price": price, "signal": signal}

    except Exception as e:
        print("❌ Lỗi xử lý webhook:", e)
        return {"status": "error", "detail": str(e)}
