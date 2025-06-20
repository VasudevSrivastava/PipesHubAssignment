import datetime as dt
import time
import threading
import os
from order_management import OrderManagement, OrderRequest, RequestType, ResponseType, OrderResponse


class TestOrderManagement(OrderManagement):
    def send(self, request: OrderRequest) -> None:
        print(f"[SEND] {request.orderId}")
        self.timestamp_logs[request.orderId] = time.time()

    def send_logon(self):
        print("[LOGON]")

    def send_logout(self):
        print("[LOGOUT]")

def run_test():
    now = dt.datetime.now()
    logon_time = (now + dt.timedelta(seconds=2)).time()
    logout_time = (now + dt.timedelta(seconds=10)).time()

    system = TestOrderManagement(logon_time, logout_time, limit_per_second=2)

    def simulate():
        system.on_data_request(OrderRequest(0, 100.0, 10, 'B', 1, RequestType.New))
        time.sleep(3)  #wait for logon

        #Direct send (under limit)
        system.on_data_request(OrderRequest(1, 100.0, 10, 'B', 1, RequestType.New))
        system.on_data_request(OrderRequest(2, 101.0, 20, 'S', 2, RequestType.New))

        #Throttled orders
        system.on_data_request(OrderRequest(3, 102.0, 30, 'B', 3, RequestType.New))
        system.on_data_request(OrderRequest(4, 103.0, 40, 'S', 4, RequestType.New))
        system.on_data_request(OrderRequest(5, 104.0, 40, 'S', 5, RequestType.New))

        #Modify queued order
        system.on_data_request(OrderRequest(5, 150.0, 99, 'B', 3, RequestType.Modify))

        #Cancel queued order
        system.on_data_request(OrderRequest(4, 0, 0, 'S', 4, RequestType.Cancel))

        #Simulate response
        time.sleep(2)
        system.on_data_response(OrderResponse(1, ResponseType.Accept))
        system.on_data_response(OrderResponse(3, ResponseType.Reject))

    threading.Thread(target=simulate).start()

    time.sleep(12)  #wait for test to complete
    print("[TEST DONE]")

    #Print response logs
    with open("response_logs.txt") as f:
        print("[LOG FILE]")
        print(f.read())

if __name__ == "__main__":
    run_test()
