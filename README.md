# REST and gRPC Service Interaction

This lab implements the same Order -> Inventory interaction using REST/HTTP
and gRPC. The inventory contains `item-123` (10 units) and `item-456` (2
units). Both inventory services support a temporary delay controlled by
`INVENTORY_DELAY_SECONDS`.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The generated files `inventory_pb2.py` and `inventory_pb2_grpc.py` are
included. Regenerate them after changing `inventory.proto` with:

```bash
python -m grpc_tools.protoc -I. \
  --python_out=. --grpc_python_out=. inventory.proto
```

## REST version

Start the Inventory Service in one terminal:

```bash
python inventory.py
```

Start the Order Service in another terminal:

```bash
python rest.py
```

The Order Service calls `http://localhost:5001/inventory/check` with a
two-second timeout. The inventory URL can be changed with
`INVENTORY_SERVICE_URL`, and the timeout can be changed with
`INVENTORY_SERVICE_TIMEOUT_SECONDS`.

Successful request:

```bash
curl -i -X POST http://localhost:5000/order \
  -H 'Content-Type: application/json' \
  -d '{"item_id":"item-123","quantity":2}'
```

Successful response:

```text
HTTP/1.1 201 CREATED
Content-Type: application/json

{"item_id":"item-123","message":"Order accepted","quantity":2}
```

Unavailable inventory returns `409 CONFLICT`:

```bash
curl -i -X POST http://localhost:5000/order \
  -H 'Content-Type: application/json' \
  -d '{"item_id":"item-456","quantity":3}'
```

### REST timeout evidence

Stop the normal inventory process and restart it with a delay longer than the
Order Service timeout:

```bash
INVENTORY_DELAY_SECONDS=3 python inventory.py
curl -i -X POST http://localhost:5000/order \
  -H 'Content-Type: application/json' \
  -d '{"item_id":"item-123","quantity":1}'
```

The expected result is:

```text
HTTP/1.1 504 GATEWAY TIMEOUT
{"error":"Inventory service request timed out"}
```

The Order Service remains running. This can be verified immediately with:

```bash
curl -i http://localhost:5000/health
```

Expected response:

```text
HTTP/1.1 200 OK
{"status":"ok"}
```

## gRPC version

The gRPC contract is defined in [inventory.proto](inventory.proto). Start the
gRPC Inventory Service:

```bash
python grpc_inventory.py
```

Start the gRPC Order Service in another terminal:

```bash
python grpc_order.py
```

The Order Service calls the Inventory Service at `localhost:50051` with a
two-second gRPC deadline. A successful order request is:

```bash
python grpc_client.py item-123 2
```

Successful response:

```text
message=Order accepted, item_id=item-123, quantity=2
```

### gRPC deadline evidence

Stop the normal gRPC inventory process and restart it with a delay longer than
the Order Service deadline:

```bash
INVENTORY_DELAY_SECONDS=3 python grpc_inventory.py
python grpc_client.py item-123 1
```

The expected output from the Order Service is:

```text
Inventory service exceeded gRPC deadline
gRPC order failed: FAILED_PRECONDITION: Order could not be accepted
```

The gRPC Order Service remains running because the deadline is handled inside
`OrderService.place_order` rather than terminating the server. Run the client
again, or inspect the server terminal, to verify it is still accepting calls.

## Comparison

REST uses human-readable JSON over HTTP, which made it easy to test with `curl`
and inspect status codes directly. gRPC required a `.proto` contract and
generated Python stubs, but it provided strongly typed request and response
messages. REST communicates timeout failure through an HTTP `504` response,
while gRPC communicates it through a deadline exception and a gRPC status
code. The gRPC deadline is part of the call itself, whereas the REST timeout
is configured on the HTTP client request. Both implementations kept the Order
Service running by catching the downstream failure at the call boundary.
