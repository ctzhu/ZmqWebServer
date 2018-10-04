import zmq
import time
import sys

port = "12346"

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://127.0.0.1:%s" % port)

while True:
    #  Wait for next request from client
    time.sleep(0.3)
    socket.send(b"World from")
    message = socket.recv()
    print("Received request: ", message)
