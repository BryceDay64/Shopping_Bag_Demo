# this is the pi
import socket
import time


HOST = "127.0.0.1"  # The server's hostname or IP address
PORT = 65432  # The port used by the server

# cap = cv2.VideoCapture(0)
# cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
# cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    while True:
        print('ready')
        message = "Send me info"
        s.sendall(str.encode(message, 'utf-8'))

        data = s.recv(1024)

        if data.decode() == "end":
            print('end')
            break

        else:
            info = data.decode().split()
            info = [info[0], info[1], info[2]]
            print(info)

        time.sleep(2)
