from fastapi import FastAPI, Request
import redis
from datetime import datetime
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
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1383078255451439107/IiJgnpDzIsZc5-kERTL7r6x55iBXFex5MVAJx7GsN2eLIBpNiajzQ6XtH4hDaaIv5m8I"  # 🔁 Thay bằng webhook thật của bạn

def send_discord_alert(message: str):
    payload = {
        "content": message  # Discord sẽ hiển thị nội dung trong "content"
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

        # Lấy thông tin cần thiết
        symbol = data.get("symbol", "UNKNOWN")
        price = str(data.get("price", "0"))
        timestamp = datetime.utcnow().isoformat()

        # Lưu vào Redis hash
        key = f"price:{symbol}"
        r.hset(key, mapping={
            "price": price,
            "time": timestamp
        })

        # Đẩy vào Redis Stream
        stream_key = "stream:prices"
        r.xadd(stream_key, {
            "symbol": symbol,
            "price": price,
            "time": timestamp
        }, maxlen=1000, approximate=True)

        # Gửi thông báo Discord
        send_discord_alert(f"📊 `{symbol}` vừa cập nhật giá **{price}** lúc `{timestamp}`")

        print(f"✅ Đã lưu {key} và đẩy vào stream {stream_key}")
        return {"status": "ok", "symbol": symbol, "price": price}

    except Exception as e:
        print("❌ Lỗi xử lý webhook:", e)
        return {"status": "error", "detail": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
