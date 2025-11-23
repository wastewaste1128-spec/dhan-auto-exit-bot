import os
import time
from dhanhq import dhanhq

# -------------------------------------------------------
# Load credentials from environment variables (SAFE)
# -------------------------------------------------------
CLIENT_ID = os.getenv("DHAN_CLIENT_ID")
ACCESS_TOKEN = os.getenv("DHAN_ACCESS_TOKEN")
API_KEY = os.getenv("DHAN_API_KEY")
SECRET_KEY = os.getenv("DHAN_SECRET_KEY")

# -------------------------------------------------------
# Safety checks
# -------------------------------------------------------
if not CLIENT_ID or not ACCESS_TOKEN:
    raise Exception("⚠️ Environment variables missing. Add keys in Render → Environment Variables")

# -------------------------------------------------------
# Initialize DHAN API
# -------------------------------------------------------
dhan = dhanhq(clientId=CLIENT_ID, accessToken=ACCESS_TOKEN)

# -------------------------------------------------------
# Your trading logic here
# -------------------------------------------------------
def run_bot():
    print("Bot started...")

    while True:
        try:
            # Example: Fetch positions
            positions = dhan.get_positions()
            print("Current positions:", positions)

            # Add your logic here:
            # place orders, modify orders, exit positions, etc.

        except Exception as e:
            print("Error:", e)

        time.sleep(5)  # avoid rate limit, adjust as needed


# -------------------------------------------------------
# Main function
# -------------------------------------------------------
if __name__ == "__main__":
    run_bot()
