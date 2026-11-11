import base64
from datetime import datetime
from flask import Flask, jsonify, request
import os
import requests

app = Flask(__name__)

CONSUMER_KEY = os.environ.get("CONSUMER_KEY")
CONSUMER_SECRET = os.environ.get("CONSUMER_SECRET")
BUSINESS_SHORTCODE = os.environ.get("BUSINESS_SHORTCODE", "174379")
PASSKEY = os.environ.get("PASSKEY")

def get_daraja_access_token():
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    try:
        r = requests.get(url, auth=(CONSUMER_KEY, CONSUMER_SECRET))
        return r.json().get("access_token")
    except Exception as e:
        print("Error getting token:", e)
        return None

@app.route("/api/stkpush", methods=["POST"])
def initiate_stk_push():
    data = request.json
    phone = data.get("phone")
    amount = data.get("amount")
    order_id = data.get("order_id")

    access_token = get_daraja_access_token()
    if not access_token:
        return jsonify({"error": "Failed to connect to M-Pesa gateway"}), 500

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password_str = f"{BUSINESS_SHORTCODE}{PASSKEY}{timestamp}"
    password = base64.b64encode(password_str.encode()).decode("utf-8")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    callback_url = "https://your-render-app-name.onrender.com/api/callback"

    payload = {
        "BusinessShortCode": BUSINESS_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": BUSINESS_SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": callback_url,
        "AccountReference": f"Order_{order_id}",
        "TransactionDesc": "Ecommerce Payment"
    }

    response = requests.post(
        "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processjson",
        json=payload,
        headers=headers
    )
    return jsonify(response.json())

@app.route("/api/callback", methods=["POST"])
def mpesa_callback():
    callback_data = request.get_json()
    print("--- M-PESA CALLBACK RECEIVED ---")
    print(callback_data)
    return jsonify({"ResultCode": 0, "ResultDesc": "Success"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)