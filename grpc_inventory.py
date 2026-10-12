import os
import time
from concurrent import futures

import grpc

import inventory_pb2
import inventory_pb2_grpc

INVENTORY = {
    "item-123": 10,
    "item-456": 2,
}
INVENTORY_DELAY_SECONDS = float(os.getenv("INVENTORY_DELAY_SECONDS", "0"))


class InventoryService(inventory_pb2_grpc.InventoryServiceServicer):
    def CheckInventory(self, request, context):
        if not request.item_id.strip() or request.quantity <= 0:
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "item_id must be non-empty and quantity must be positive",
            )

        if INVENTORY_DELAY_SECONDS > 0:
            time.sleep(INVENTORY_DELAY_SECONDS)

        available_quantity = INVENTORY.get(request.item_id, 0)
        return inventory_pb2.InventoryResponse(
            available=available_quantity >= request.quantity,
            remaining_quantity=available_quantity,
        )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    inventory_pb2_grpc.add_InventoryServiceServicer_to_server(
        InventoryService(), server
    )
    server.add_insecure_port("[::]:50051")
    server.start()
    print("gRPC inventory service listening on :50051", flush=True)
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
