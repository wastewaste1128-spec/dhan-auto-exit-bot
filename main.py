import time
from dhanhq import dhanhq
import os

# Load DHAN credentials from environment variables
client_id = os.getenv("DHAN_CLIENT_ID")
access_token = os.getenv("DHAN_ACCESS_TOKEN")

dhan = dhanhq(client_id, access_token)

TARGET_POINTS = 1  # Exit at +1 point over entry price

def get_positions():
    """Fetch live Dhan positions"""
    try:
        pos = dhan.get_positions()
        return pos
    except Exception as e:
        print("Error fetching positions:", e)
        return []

def get_ltp(symbol):
    """Fetch LTP"""
    try:
        quote = dhan.get_quote(symbol)
        return quote["LTP"]
    except:
        return None

def exit_order(symbol, qty):
    """Place market sell order"""
    print(">>> PLACING EXIT ORDER <<<")
    try:
        resp = dhan.place_order(
            tag="AUTOEXIT",
            transaction_type="SELL",
            exchange_segment="NFO",
            product_type="INTRADAY",
            order_type="MARKET",
            validity="DAY",
            security_id=symbol,
            quantity=qty
        )
        print("Exit Response:", resp)
    except Exception as e:
        print("Exit Error:", e)

def monitor_position(symbol, entry_price, qty):
    """Monitor LTP until +1 point target is hit"""
    target = entry_price + TARGET_POINTS
    print(f"Monitoring: Symbol={symbol}, Entry={entry_price}, Target={target}")

    while True:
        ltp = get_ltp(symbol)
        if ltp:
            print("LTP:", ltp)

            if ltp >= target:
                print(">>> TARGET HIT <<<")
                exit_order(symbol, qty)
                return

        time.sleep(0.5)

if __name__ == "__main__":
    print("AUTO EXIT BOT STARTED... Waiting for your manual trade...")

    last_position_id = None

    while True:
        positions = get_positions()

        if positions and len(positions) > 0:
            pos = positions[0]

            position_id = pos["positionId"]
            symbol = pos["securityId"]
            entry_price = float(pos["buyAvg"])
            qty = int(pos["netQty"])

            if qty > 0 and position_id != last_position_id:
                print("\n>>> NEW POSITION DETECTED <<<")
                print(pos)

                last_position_id = position_id

                monitor_position(symbol, entry_price, qty)

        time.sleep(1)
