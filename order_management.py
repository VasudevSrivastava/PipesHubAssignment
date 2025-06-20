from dataclasses import dataclass
import threading
import datetime as dt
import time
from enum import Enum
from collections import deque


#dataclass decorator used instead of plain classes for more concise and clean code
@dataclass
class Logon:
    username : str
    password : str

@dataclass
class Logout:
    username : str 

class RequestType(Enum):
    Unknown = 0
    New = 1
    Modify = 2
    Cancel = 3

class ResponseType(Enum):
    Unknown = 0
    Accept = 1
    Reject = 2

@dataclass
class OrderRequest:
    symbolId : int
    price : float 
    qty : int 
    side : str 
    orderId : int
    request_type : RequestType

@dataclass
class OrderResponse:
    orderId : int
    responseType : ResponseType


class OrderManagement:

    def __init__(self, logon_time : dt.time, logout_time: dt.time, limit_per_second : int):
        self.logon_time = logon_time
        self.logout_time = logout_time
        self.limit_per_second = limit_per_second
        self.trading_active = False
        self.last_logon_date = None
        self.last_logout_date = None
        self.running = True
        self.schedule_thread = threading.Thread(target=self.check_schedule, daemon=True)
        self.schedule_thread.start()

        self.lock = threading.Lock()
        self.previous_second = None
        self.current_request_count = 0
        self.request_queue = deque()
        self.request_map = dict()
        self.send_requests_thread = threading.Thread(target=self.throttle_queue, daemon=True)
        self.send_requests_thread.start()

        self.timestamp_logs = dict()

    def check_schedule(self): #responsible for sending logon and logout requests
        while self.running:
            current_date = dt.datetime.now().date()
            current_time = dt.datetime.now().time()
            if (self.last_logon_date != current_date and 
                current_time >= self.logon_time):
                self.trading_active = True
                self.send_logon()
                self.last_logon_date = current_date
            if (self.last_logout_date != current_date and 
                current_time >= self.logout_time):
                self.trading_active = False
                self.send_logout()
                self.last_logout_date = current_date
            time.sleep(0.1)
    
    def throttle_queue(self): #handles the order queue and hashmap
        while self.running:
            current_time = int(time.time())
            with self.lock:
                if current_time != self.previous_second:
                    self.previous_second = current_time
                    self.current_request_count = 0
                    while self.current_request_count < self.limit_per_second and self.request_queue:

                        top = self.request_queue.popleft()
                        if top.orderId in self.request_map:
                            self.send(top)
                            #print(top)
                            self.timestamp_logs[top.orderId] = time.time()
                            del self.request_map[top.orderId]
                            self.current_request_count += 1
                    
            time.sleep(0.1)
                    
                

    def on_data_request(self, request : OrderRequest) -> None :
        if not self.trading_active:
            print("Trading not active yet")
            return
        
        with self.lock:
            if request.request_type == RequestType.Modify:
                queued_request = self.request_map.get(request.orderId)
                if queued_request: #ensures wrong requests don't cause errors
                    queued_request.qty = request.qty
                    queued_request.price = request.price
                
            elif request.request_type == RequestType.Cancel:
                queued_request = self.request_map.get(request.orderId)
                if queued_request:
                    del self.request_map[queued_request.orderId]
                
                
            else:
                if self.current_request_count < self.limit_per_second:
                    self.send(request)
                 #   print(request)
                    self.timestamp_logs[request.orderId] = time.time()
                    self.current_request_count += 1
                else:
                    self.request_queue.append(request)
                    self.request_map[request.orderId] = request

    def on_data_response(self, response : OrderResponse) -> None:
        with self.lock:
            logged_entry = self.timestamp_logs.get(response.orderId)
            if not logged_entry:
                print("Order does not exist")
                return
        round_trip_latency = time.time() - logged_entry
        text = f"{response.responseType.name}, {response.orderId}, {round_trip_latency} \n"
        with open("response_logs.txt", 'a') as logfile:
            logfile.write(text)

    def send(self, request : OrderRequest) -> None :
        pass

    def send_logon(self):
        pass

    def send_logout(self):
        pass