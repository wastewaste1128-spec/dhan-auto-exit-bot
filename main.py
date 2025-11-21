import requests
import time
from dhanhq import dhanhq
import os

# Load API keys from environment variables (Render will store securely)
client_id = os.getenv("DHAN_CLIENT_ID")
access_token = os.getenv("DHAN_ACCESS_TOKEN")

dhan = dhanhq(client_id, access_token)

TARGET_POINTS = 1   # fixed target of +1 point


def get_ltp(symbol):
    """Fetch live price"""
    try:
        res = dhan.get_quote(symbol)
        return res["LTP"]
    except:
        return None


def place_exit_order(symbol, quantity):
    """Place SELL exit order"""
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


def monitor_trade(symbol, entry_price, quantity):
    """Monitor price & exit at +1 point"""
    target = entry_price + TARGET_POINTS
    print(f"Entry: {entry_price}, Target: {target}")

    while True:
        ltp = get_ltp(symbol)
        print("LTP:", ltp)

        if ltp is None:
            time.sleep(1)
            continue

        if ltp >= target:
            print("TARGET HIT. Exiting...")
            place_exit_order(symbol, quantity)
            break

        time.sleep(0.5)


if __name__ == "__main__":
    print("Bot running... waiting for manual entry")

    # You will manually enter your trade through Dhan.
    # After placing trade, enter your:
    # 1. symbol_token
    # 2. entry price
    # 3. quantity

    symbol = input("Enter option token: ")
    entry = float(input("Enter entry price: "))
    qty = int(input("Enter quantity: "))

    monitor_trade(symbol, entry, qty)
