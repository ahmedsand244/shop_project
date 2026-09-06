

import requests
from django.conf import settings

# Paymob Config
PAYMOB_API_KEY = 'ZXlKaGJHY2lPaUpJVXpVeE1pSXNJblI1Y0NJNklrcFhWQ0o5LmV5SmpiR0Z6Y3lJNklrMWxjbU5vWVc1MElpd2ljSEp2Wm1sc1pWOXdheUk2TVRBME1qRTVOaXdpYm1GdFpTSTZJakUzTkRZMk5qUTBNek11T0RFeU5UVXlJbjAuTF9oMmhOWWJGMXFVRTdXb0dMVlV4ZzhSTWVFdFUzWGp0cU54VGZ1THhoNUs5V1lHbkVJcDJ4TkFjTkRwdUNTTnlQRUZNdy00cGZxN0Y2OHdQMXhHVmc='
PAYMOB_IFRAME_ID_CARD = '919350'
PAYMOB_IFRAME_ID_VODAFONE = '919351'  # ← عدلها بعد ما تنشئ Iframe لفودافون
INTEGRATION_ID_CARD = '5081578'
INTEGRATION_ID_VODAFONE = '5083545'


def get_auth_token():
    url = "https://accept.paymob.com/api/auth/tokens"
    data = {"api_key": PAYMOB_API_KEY}
    response = requests.post(url, json=data)
    return response.json()["token"]


def create_order(token, amount_cents):
    url = "https://accept.paymob.com/api/ecommerce/orders"
    data = {
        "auth_token": token,
        "delivery_needed": False,
        "amount_cents": amount_cents,
        "currency": "EGP",
        "items": []
    }
    response = requests.post(url, json=data)
    return response.json()


def get_payment_key(token, order_id, amount_cents, user_data, integration_id):
    url = "https://accept.paymob.com/api/acceptance/payment_keys"
    data = {
        "auth_token": token,
        "amount_cents": amount_cents,
        "expiration": 3600,
        "order_id": order_id,
        "billing_data": {
            "apartment": "NA",
            "email": user_data.get("email", "arthmd0z@gmail.com"),
            "floor": "NA",
            "first_name": user_data.get("first_name", "Test"),
            "street": "NA",
            "building": "NA",
            "phone_number": user_data.get("phone", "01000000000"),
            "shipping_method": "NA",
            "postal_code": "NA",
            "city": "NA",
            "country": "NA",
            "last_name": user_data.get("last_name", "User"),
            "state": "NA"
        },
        "currency": "EGP",
        "integration_id": integration_id,
    }

    response = requests.post(url, json=data)
    result = response.json()
    if "token" not in result:
        raise ValueError(f"Failed to get payment key: {result}")
    return result["token"]








































