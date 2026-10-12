import sys

import grpc

import inventory_pb2
import inventory_pb2_grpc


def main():
    item_id = sys.argv[1] if len(sys.argv) > 1 else "item-123"
    quantity = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    with grpc.insecure_channel("localhost:50052") as channel:
        order = inventory_pb2_grpc.OrderServiceStub(channel)
        try:
            response = order.PlaceOrder(
                inventory_pb2.InventoryRequest(item_id=item_id, quantity=quantity),
                timeout=3,
            )
        except grpc.RpcError as error:
            print(f"gRPC order failed: {error.code().name}: {error.details()}")
            return 1
        print(
            f"message={response.message}, "
            f"item_id={response.item_id}, quantity={response.quantity}"
        )
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
