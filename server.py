from flask import Flask, request

app = Flask(__name__)

# Health check
@app.route("/")
def home():
    return "Bot Running Successfully!"


# 1️⃣ Simple test - server working
@app.route("/ping", methods=["GET"])
def ping():
    return {"status": "ok", "message": "Server active"}, 200


# 2️⃣ Deep test - send dummy order data (no order placed)
@app.route("/test", methods=["POST"])
def test():
    data = request.json
    print("TEST DATA RECEIVED:", data)
    return {
        "message": "Test successful! No real order placed.",
        "received": data
    }, 200


# 3️⃣ Dry-run for future trading endpoint (SAFE)
@app.route("/place_order", methods=["POST"])
def place_order():
    data = request.json
    
    # If dry_run flag = true → DO NOT place real trade
    if data.get("dry_run") == True:
        return {
            "message": "Dry-run mode: No real order placed.",
            "received": data
        }, 200
    
    # Real trading code will go here later (only after testing)
    return {
        "message": "Real trading disabled in testing mode. Add 'dry_run': true to test safely."
    }, 403


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
