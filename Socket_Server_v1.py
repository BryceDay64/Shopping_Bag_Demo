# This server code is meant to be run on a laptop with the UR20 connecting as a client.
import socket
import cv2
import keyboard

HOST = ""  # I might be able to set the server IP address with this. Leaving it blank uses the current IP address.
PORT = 65432  # Port to listen on (non-privileged ports are > 1023)

# Set up for the socket connection
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
	# I need to mess with this more. I think it will set the IP address and port number of the server.
	s.bind((HOST, PORT))

	# This opens the server for connections by clients.
	s.listen()
	conn, addr = s.accept()

	# Run the following code when a client connects
	with conn:

		# print the IP address of the connected client
		print("Connected by " + str(addr[0]))
		while True:

			# receive messages from the client
			data = conn.recv(1024)

			# if this is not what we expect quit. (I think)
			if not data:
				break

			# Message sent by the UR20 to say that it is ready to receive more data.
			if data.decode() == "Send me info":

				# This will loop through the new opencv frames
				while True:
					# TODO: Pull in the computer vision functionality here. (Bag_Detection_v1.py)

					# Run this when object is found (keyboard interrupt for now)
					if keyboard.is_pressed('a'):  # if object found
						# This should be the info variable passed by Bag_Detection_v1.py,
						# but was made a string for testing purposes.
						message = "info"
						break

					# Run this to end the demo (will stay keyboard interrupt)
					if keyboard.is_pressed('s'):  # if we want to stop the code
						message = "end"
						break

			# Sends message to UR20 (either the bag info or the end command)
			conn.sendall(str.encode(message, 'utf-8'))
