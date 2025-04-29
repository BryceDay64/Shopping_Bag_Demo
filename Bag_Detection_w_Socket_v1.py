import socket
import cv2
import numpy as np


def compare_frames(frame_1, frame_2, mask_th: int, erode_iteration: int, dilate_iteration: int = None):
    """
    :param frame_1: The more stable frame
    :param frame_2: The frame were are checking for changes.
    :param mask_th: The threshold for masking absolute pixel difference (larger is more aggressive)
    :param erode_iteration: How many erosion iterations. Will be larger if the threshold is more aggressive.
    :param dilate_iteration: Defaults to match erosion iterations to keep the object the same size.
    :return: Black and white image of the difference between the two images.
             Image will be completely black if there is no difference.
    """

    # Set dilate_iteration equal to erode_iteration by default unless overwritten
    if dilate_iteration is None:
        dilate_iteration = erode_iteration

    # blur each image
    blurred_frame_1 = cv2.GaussianBlur(frame_1, (5, 5), 0)
    blurred_frame_2 = cv2.GaussianBlur(frame_2, (5, 5), 0)

    # Absolute difference between the two figures
    diff = cv2.absdiff(blurred_frame_1, blurred_frame_2)

    # Grayscale the difference between the images
    mask = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

    # Create a mask where only pixels with a difference larger than the threshold are kept non-black
    diff_mask = mask > mask_th

    # Apply the mask to frame_2
    frame_diff = np.zeros_like(frame_2, np.uint8)
    frame_diff[diff_mask] = frame_2[diff_mask]

    # Blur the masked frame_2
    frame_diff = cv2.GaussianBlur(frame_diff, (5, 5), 0)

    # Change the image to grayscale
    frame_diff = cv2.cvtColor(frame_diff, cv2.COLOR_BGR2GRAY)

    # Threshold the image so that everything that is not black becomes white
    (thresh, frame_diff) = cv2.threshold(frame_diff, 1, 255, cv2.THRESH_BINARY)

    # Erode the result to get rid of any holes  or lines through the white blob
    frame_diff = cv2.erode(frame_diff, kernel, iterations=erode_iteration)

    # Dilate the white blob to return it closer to its original size
    frame_diff = cv2.dilate(frame_diff, kernel, iterations=dilate_iteration)
    return frame_diff


HOST = ""  # I might be able to set the server IP address with this. Leaving it blank uses the current IP address.
PORT = 65432  # Port to listen on (non-privileged ports are > 1023)

cap = cv2.VideoCapture(0)

# The area used to dilate and erode images
kernel = np.ones((5, 5), np.uint8)

# Initialize action, which determines if something is moving in frame.
action = False

# Initialize frame counter
frame_num = 0

# Initialize boolean that determines if the detector is on. This is purely for aesthetic purposes in the output frame.
blob_on = False

# Initialize stable frame and previous frame so that PyCharm stops warning me that it could be undefined.
stable_frame = None
previous_frame = None

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

                # While we have the video going.
                while cap.isOpened():

                    # Ret determines if a frame exists and frame is the resulting frame.
                    ret, frame = cap.read()

                    # Frame width and height in pixels
                    width = cap.get(3)
                    height = cap.get(4)

                    # if frame is not retained then break and close. For a video file this breaks at the end of the video.
                    # For live video this should trigger if there are issues with the camera.
                    if not ret:
                        print("Frame not found")
                        break

                    # Increment the frame counter
                    frame_num += 1

                    # Aesthetic: Keeps holes from flashing when the contour detector flashes on and off.
                    if blob_on:
                        blob_on = False

                    # TODO:The following checks if it the first frame of the video capture, and sets that to be the stable frame.
                    #  This works but is not best practice.
                    # Initialize the first frame as the stable frame.
                    if frame_num == 1:
                        stable_frame = frame
                        # set tmpArea to a black frame the same size as the frame.
                        tmpArea = np.zeros((int(width), int(height), 3))

                    else:
                        # TODO: These values may be overfit to the video and is likely too aggressive for the floor in the robotics
                        #  institute (the grout lines in my kitchen where similar to the color of the sacs).

                        # This compares the current frame to a frame that has no objects in it.
                        # The difference in the frames should be new objects in the frame.
                        # If we have been detecting movement this is not an object we want to pick up
                        # (it could be a person setting down the object that we want to pick up).
                        # If there has not been movement, then we detect the object and pick it up.
                        # TODO: The mask threshold and erode iterations likely need to be lowered in the institute setting.
                        canvas = compare_frames(stable_frame, frame, 40, 7)

                        # If the frame is the same as the stable frame the following code makes the current frame the stable frame.
                        # The idea is that this would update the frame if new small objects moved into the frame,
                        # but it creates issues when a moving object pauses for a moment in frame.
                        if np.all(canvas == 0):
                            # This does nothing. I commented out the code that updates the stable frame
                            # which causes the if statement to throw an error. This was my quick fix,
                            # that allows for this functionality to be easily reimplemented if need be.
                            i = 1
                            # stable_frame = frame

                        # If the current frame is different then the stable frame.
                        else:

                            # If movement has not previously detected start capturing movement using "previous frame" and
                            # set action to True to indicate that we are tracking motion.
                            if not action:
                                previous_frame = frame
                                action = True

                            # TODO: The following code detects an object after motion has been detected,
                            #  but has no way of turning off the motion detection unless an object has been found.

                            # If movement has been previously detected.
                            else:
                                # Determine if the last frame is the same as the current frame. This check is much less aggressive.
                                # TODO: ADJUST ME TO THE INSTITUTE SETTING AFTER THE CANVAS VARIABLE HAS BEEN FINE TUNED
                                check = compare_frames(previous_frame, frame, 2, 3)

                                # Uncomment this to fine tune the compare_frames parameters to your setting.
                                cv2.imshow("check", check)

                                # If the last frame is the same as this frame look for the object to be picked up.
                                if np.all(check == 0):

                                    # dilate then erode to fill any holes that may appear in the blobs
                                    canvas = cv2.dilate(canvas, kernel, iterations=5)
                                    canvas = cv2.erode(canvas, kernel, iterations=5)

                                    # create a black image the same size the normal one
                                    tmpArea = np.zeros(frame.shape)

                                    # draw the contour around the blob, and draw it on the black image filled in
                                    contours = cv2.findContours(canvas, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)[0]
                                    c = max(contours, key=cv2.contourArea)
                                    cv2.drawContours(tmpArea, [c], 0, (255, 255, 255), cv2.FILLED)

                                    # calculate the centroid and place it on the image
                                    M = cv2.moments(c)
                                    cx = int(M['m10'] / M['m00'])
                                    cy = int(M['m01'] / M['m00'])
                                    cv2.circle(tmpArea, (cx, cy), 5, (0, 0, 255), -1)

                                    # Draw an ellipse around the contour
                                    e = cv2.fitEllipse(c)
                                    cv2.ellipse(tmpArea, e, (0, 255, 0), 2)

                                    # Determine the major axis of the ellipse
                                    x1 = int(np.round(cx + e[1][1] / 2 * np.cos((e[2] + 90) * np.pi / 180.0)))
                                    y1 = int(np.round(cy + e[1][1] / 2 * np.sin((e[2] + 90) * np.pi / 180.0)))
                                    x2 = int(np.round(cx + e[1][1] / 2 * np.cos((e[2] - 90) * np.pi / 180.0)))
                                    y2 = int(np.round(cy + e[1][1] / 2 * np.sin((e[2] - 90) * np.pi / 180.0)))

                                    # Determine the minor axis of the ellipse
                                    x3 = int(np.round(cx + e[1][0] / 2 * np.cos((e[2] + 180) * np.pi / 180.0)))
                                    y3 = int(np.round(cy + e[1][0] / 2 * np.sin((e[2] + 180) * np.pi / 180.0)))
                                    x4 = int(np.round(cx + e[1][0] / 2 * np.cos((e[2]) * np.pi / 180.0)))
                                    y4 = int(np.round(cy + e[1][0] / 2 * np.sin((e[2]) * np.pi / 180.0)))

                                    # Draw the major and minor axes
                                    cv2.line(tmpArea, (x1, y1), (x2, y2), (255, 255, 0), 2)
                                    cv2.line(tmpArea, (x3, y3), (x4, y4), (0, 0, 255), 2)

                                    # Change tmpArea to canvas so the imshow output works nicely
                                    canvas = tmpArea

                                    # A list variable containing the x and y position of the centroid and the angle of the minor axis
                                    message = [cx, cy, e[2] - 90]

                                    # This says blob detect is on for aesthetic purposes in the display below.
                                    blob_on = True

                                    # Turn off the detection of motion as an object has been found.
                                    # If running the code as is this causes the detector to flicker on and off.
                                    # If used with the UR20 this will not be an issue
                                    # because the robot will not move and pick up the bag in one frame.
                                    action = False

                                # If the current frame is not the same as the previous frame then make the current frame the
                                # previous in preparation for the next frame.
                                else:
                                    previous_frame = frame

                        # If canvas didn't go through detection on the other frame then this will match the dilation and erosion so that
                        # there's no flicker in imshow. This is purely aesthetic.
                        if not blob_on:
                            canvas = cv2.dilate(canvas, kernel, iterations=5)
                            canvas = cv2.erode(canvas, kernel, iterations=5)

                        # Display the difference between the current frame and the stable frame to see the objects.
                        cv2.imshow('frame', canvas)

                        # If the "q" key is pressed break and close.
                        if cv2.waitKey(1) == ord('esc'):
                            message = 'end'
                            break
                    '''
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
                    '''

            # Sends message to UR20 (either the bag info or the end command)
            conn.sendall(str.encode(message, 'utf-8'))

cap.release()
cv2.destroyAllWindows()
