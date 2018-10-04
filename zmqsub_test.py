import zmq
import time
import sys

port = "12345"

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://127.0.0.1:%s" % port)
socket.setsockopt(zmq.SUBSCRIBE, b'')

while True:
    #  Wait for next request from client
    time.sleep(0.3)
    message = socket.recv_multipart()
    print("Received request: ", message)
