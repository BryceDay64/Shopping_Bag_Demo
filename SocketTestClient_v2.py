# this is the pi
import socket
import cv2
import numpy as np

HOST = "127.0.0.1"  # The server's hostname or IP address
PORT = 65432  # The port used by the server

# cap = cv2.VideoCapture(0)
# cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
# cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    while True:
        message = input("enter message: ")
        if message == "end":
            break
        s.sendall(str.encode(message, 'utf-8'))
        data = s.recv(1024)
        print("Recieved " + data.decode())

        key = cv2.waitKey(1)

# cap.release()
cv2.destroyAllWindows()