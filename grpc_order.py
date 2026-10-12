import os
from concurrent import futures

import grpc

import inventory_pb2
import inventory_pb2_grpc

INVENTORY_SERVICE_ADDRESS = os.getenv(
    "INVENTORY_SERVICE_ADDRESS",
    "localhost:50051",
)
GRPC_DEADLINE_SECONDS = float(os.getenv("GRPC_DEADLINE_SECONDS", "2"))


class OrderService:
    def __init__(self):
        self.channel = grpc.insecure_channel(INVENTORY_SERVICE_ADDRESS)
        self.inventory = inventory_pb2_grpc.InventoryServiceStub(self.channel)

    def place_order(self, item_id, quantity):
        try:
            response = self.inventory.CheckInventory(
                inventory_pb2.InventoryRequest(item_id=item_id, quantity=quantity),
                timeout=GRPC_DEADLINE_SECONDS,
            )
        except grpc.RpcError as error:
            if error.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                print("Inventory service exceeded gRPC deadline", flush=True)
                return False
            print(f"Inventory service error: {error.code().name}", flush=True)
            return False

        if not response.available:
            print("Item is not available in the requested quantity", flush=True)
            return False
        print(
            f"Order accepted: item_id={item_id}, quantity={quantity}",
            flush=True,
        )
        return True


class OrderGrpcService(inventory_pb2_grpc.OrderServiceServicer):
    """Keeps the order process available while it makes inventory calls."""

    def __init__(self):
        self.order_service = OrderService()

    def PlaceOrder(self, request, context):
        if self.order_service.place_order(request.item_id, request.quantity):
            return inventory_pb2.OrderResponse(
                message="Order accepted",
                item_id=request.item_id,
                quantity=request.quantity,
            )
        context.abort(grpc.StatusCode.FAILED_PRECONDITION, "Order could not be accepted")


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    inventory_pb2_grpc.add_OrderServiceServicer_to_server(
        OrderGrpcService(), server
    )
    server.add_insecure_port("[::]:50052")
    server.start()
    print("gRPC order service listening on :50052", flush=True)
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
