import os

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

INVENTORY_SERVICE_URL = os.getenv(
    "INVENTORY_SERVICE_URL",
    "http://localhost:5001/inventory/check",
)
INVENTORY_SERVICE_TIMEOUT_SECONDS = float(
    os.getenv("INVENTORY_SERVICE_TIMEOUT_SECONDS", "2")
)


@app.post("/order")
def order():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="Request body must be a JSON object"), 400

    item_id = payload.get("item_id")
    quantity = payload.get("quantity")
    if not isinstance(item_id, str) or not item_id.strip():
        return jsonify(error="item_id must be a non-empty string"), 400
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
        return jsonify(error="quantity must be a positive integer"), 400

    try:
        inventory_response = requests.post(
            INVENTORY_SERVICE_URL,
            json={"item_id": item_id, "quantity": quantity},
            timeout=INVENTORY_SERVICE_TIMEOUT_SECONDS,
        )
        inventory_response.raise_for_status()
        inventory = inventory_response.json()
    except requests.Timeout:
        app.logger.warning("Inventory service exceeded REST timeout")
        return jsonify(error="Inventory service request timed out"), 504
    except requests.RequestException:
        app.logger.exception("Inventory service request failed")
        return jsonify(error="Inventory service unavailable"), 502
    except ValueError:
        app.logger.error("Inventory service returned invalid JSON")
        return jsonify(error="Inventory service returned an invalid response"), 502

    if not isinstance(inventory, dict) or not isinstance(inventory.get("available"), bool):
        app.logger.error("Inventory service returned an invalid response shape")
        return jsonify(error="Inventory service returned an invalid response"), 502
    if not inventory["available"]:
        return jsonify(error="Item is not available in the requested quantity"), 409

    return jsonify(
        message="Order accepted",
        item_id=item_id,
        quantity=quantity,
    ), 201


@app.get("/health")
def health():
    return jsonify(status="ok")


if __name__ == "__main__":
    app.run(port=5000)
