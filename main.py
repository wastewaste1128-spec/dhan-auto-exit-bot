import time
import os
from dhanhq import dhanhq

# Load credentials from environment variables
client_id = os.getenv("DHAN_CLIENT_ID")
access_token = os.getenv("DHAN_ACCESS_TOKEN")

dhan = dhanhq(client_id, access_token)

TARGET_POINTS = 1  # Exit after +1 point profit


def get_positions():
    """Safely get all positions."""
    try:
        pos = dhan.get_positions()
        if isinstance(pos, str):
            print("Positions API returned string:", pos)
            return []
        return pos
    except Exception as e:
        print("Position Error:", e)
        return []


def get_latest_option_position():
    """Returns latest intraday NFO option BUY position."""
    positions = get_positions()

    for p in positions:
        # Skip invalid string entries returned by API
        if not isinstance(p, dict):
            print("Invalid position entry:", p)
            continue

        if (
            p.get("exchangeSegment") == "NFO"
            and p.get("productType") == "INTRADAY"
            and p.get("positionType") == "BUY"
        ):
            return p

    return None


def get_ltp(symbol):
    """Fetch LTP for a given symbol."""
    try:
        data = dhan.get_quotes("NFO", symbol)
        return float(data.get("last_price", 0))
    except Exception as e:
        print("LTP Error:", e)
        return 0


def exit_position(symbol, qty):
    """Exit the position at market."""
    try:
        print(f"Exiting position: {symbol} | Qty: {qty}")
        res = dhan.place_order(
            security_id=symbol,
            exchange_segment="NFO",
            transaction_type="SELL",
            quantity=qty,
            order_type="MARKET",
            product_type="INTRADAY"
        )
        print("Exit response:", res)
        return res
    except Exception as e:
        print("Exit Error:", e)
        return None


def start_monitoring():
    """Main loop that monitors position and exits at +1 point profit."""
    print("Monitoring started...")

    while True:
        pos = get_latest_option_position()

        if not pos:
            print("No active BUY option position found... retrying...")
            time.sleep(5)
            continue

        symbol = pos.get("securityId")
        buy_price = float(pos.get("buyAvgPrice", 0))
        qty = int(pos.get("quantity", 0))

        ltp = get_ltp(symbol)
        pnl_points = ltp - buy_price

        print(f"Symbol: {symbol} | Buy: {buy_price} | LTP: {ltp} | P&L: {pnl_points}")

        if pnl_points >= TARGET_POINTS:
            print("Target hit! Exiting position...")
            exit_position(symbol, qty)
            time.sleep(3)
            break

        time.sleep(1)


# NOTE: No auto-start here. start_monitoring() will be called from server.py.
