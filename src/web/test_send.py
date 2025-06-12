import requests
import json

url = "https://a054-113-161-238-218.ngrok-free.app/webhook"
data = {
    "symbol": "XAUUSD",
    "side": "buy",
    "price": "2367.89",
    "trigger": "Manual test"
}

response = requests.post(url, json=data)
print("Server response:", response.json())


data = '{\"symbol\": \"XAUUSD\", \"side\": \"buy\", \"price\": \"2367.89\", \"trigger\": \"Manual Entry\"}'


data_json = json.load(data)