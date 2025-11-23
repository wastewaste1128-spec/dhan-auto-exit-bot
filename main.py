import time
import os
from dhanhq import dhanhq

# Load credentials from environment
client_id = os.getenv("DHAN_CLIENT_ID")
access_token = os.getenv("DHAN_ACCESS_TOKEN")

# Load trade details from environment
symbol = os.getenv("OPTION_TOKEN")
entry_price = float(os.getenv("ENTRY_PRICE"))
quantity = int(os.getenv("QUANTITY"))

TARGET_POINTS = 1  # +1 point target

# Initialize Dhan API
dhan = dhanhq(client_id, access_token)

def get_ltp(symbol):
    """Fetch LTP"""
    try:
        res = dhan.get_quote(symbol)
        return res["LTP"]
    except:
        return None

def place_exit_order(symbol, quantity):
    """Place market sell order"""
    print("Placing EXIT ORDER...")
    return dhan.place_order(
        tag="AUTOEXIT",
        transaction_type="SELL",
        exchange_segment="NFO",
        product_type="INTRADAY",
        order_type="MARKET",
        validity="DAY",
        security_id=symbol,
        quantity=quantity
    )

def monitor_trade():
    target = entry_price + TARGET_POINTS
    print(f"Auto Exit Bot Started")
    print(f"Symbol: {symbol}")
    print(f"Entry: {entry_price}")
    print(f"Target: {target}")

    while True:
        ltp = get_ltp(symbol)
        if ltp is None:
            print("Failed to fetch LTP... retrying...")
            time.sleep(1)
            continue

        print(f"LTP: {ltp}")

        if ltp >= target:
            print("TARGET HIT")
            place_exit_order(symbol, quantity)
            break

        time.sleep(0.5)


if __name__ == "__main__":
    monitor_trade()
