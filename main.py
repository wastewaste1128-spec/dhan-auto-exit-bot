import time
import os
from dhanhq import dhanhq

client_id = os.getenv("DHAN_CLIENT_ID")
access_token = os.getenv("DHAN_ACCESS_TOKEN")

dhan = dhanhq(client_id, access_token)
TARGET_POINTS = 1  # +1 point exit


def get_positions():
    """Get all positions safely"""
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
    """Returns latest intraday NFO option BUY position"""
    positions = get_positions()

    for p
