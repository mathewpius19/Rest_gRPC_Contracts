import os
import time

from flask import Flask, jsonify, request

app = Flask(__name__)

INVENTORY = {
    "item-123": 10,
    "item-456": 2,
}
INVENTORY_DELAY_SECONDS = float(os.getenv("INVENTORY_DELAY_SECONDS", "0"))


@app.post("/inventory/check")
def check_inventory():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="Request body must be a JSON object"), 400

    item_id = payload.get("item_id")
    quantity = payload.get("quantity")
    if not isinstance(item_id, str) or not item_id.strip():
        return jsonify(error="item_id must be a non-empty string"), 400
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
        return jsonify(error="quantity must be a positive integer"), 400

    if INVENTORY_DELAY_SECONDS > 0:
        time.sleep(INVENTORY_DELAY_SECONDS)

    available_quantity = INVENTORY.get(item_id, 0)
    return jsonify(
        available=available_quantity >= quantity,
        item_id=item_id,
        remaining_quantity=available_quantity,
    )


@app.get("/health")
def health():
    return jsonify(status="ok")


if __name__ == "__main__":
    app.run(port=5001)
