import time
from dhanhq import dhanhq
import os

client_id = os.getenv("DHAN_CLIENT_ID")
access_token = os.getenv("DHAN_ACCESS_TOKEN")

dhan = dhanhq(client_id, access_token)
TARGET_POINTS = 1  # +1 point auto exit


def get_ltp(symbol):
    try:
        q = dhan.get_quote(symbol)
        return q["LTP"]
    except:
        return None


def place_exit(symbol, qty):
    print(">>> EXIT ORDER EXECUTED <<<")
    try:
        return dhan.place_order(
            tag="AUTOEXIT",
            transaction_type="SELL",
            exchange_segment="NFO",
            product_type="INTRADAY",
            order_type="MARKET",
            validity="DAY",
            security_id=symbol,
            quantity=qty
        )
    except Exception as e:
        print("Exit Error:", e)


def start_monitoring(symbol, entry_price, qty):
    target = entry_price + TARGET_POINTS
    print(f"Monitoring Token={symbol}, Entry={entry_price}, Target={target}")

    while True:
        ltp = get_ltp(symbol)
        if ltp:
            print("LTP:", ltp)

            if ltp >= target:
                print("Target Hit!")
                place_exit(symbol, qty)
                return

        time.sleep(0.5)
