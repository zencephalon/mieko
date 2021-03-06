# USAGE
# python motion_detector.py
# python motion_detector.py --video videos/example_01.mp4

# import the necessary packages
import argparse
import datetime
import imutils
import time
import cv2
import urllib
import numpy as np

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", help="path to the video stream")
ap.add_argument("-a", "--min-area", type=int, default=500, help="minimum area size")
args = vars(ap.parse_args())

# # if the video argument is None, then we are reading from webcam
if args.get("video", None) is None:
	print "--video parameter required"
	exit()

# initialize the first frame in the video stream
firstFrame = None

stream = urllib.urlopen(args["video"])
bytes = ''

# loop over the frames of the video
while True:
	# Hacky code for manually decoding mjpeg stream
	bytes += stream.read(1024)
	a, b = bytes.find('\xff\xd8'), bytes.find('\xff\xd9')
	if a != -1 and b != -1:
		jpg, bytes = bytes[a:b+2], bytes[b+2:]
		frame = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.CV_LOAD_IMAGE_COLOR)

		motion = False

		# resize the frame, convert it to grayscale, and blur it
		frame = imutils.resize(frame, width=500)
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		gray = cv2.GaussianBlur(gray, (21, 21), 0)

		# if the first frame is None, initialize it
		if firstFrame is None:
			firstFrame = gray
			continue

		# compute the absolute difference between the current frame and
		# first frame
		frameDelta = cv2.absdiff(firstFrame, gray)
		thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]

		# dilate the thresholded image to fill in holes, then find contours
		# on thresholded image
		thresh = cv2.dilate(thresh, None, iterations=2)
		(cnts, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
			cv2.CHAIN_APPROX_SIMPLE)

		# loop over the contours
		for c in cnts:
			# if the contour is too small, ignore it
			if cv2.contourArea(c) < args["min_area"]:
				continue

			# compute the bounding box for the contour, draw it on the frame,
			# and update the text
			(x, y, w, h) = cv2.boundingRect(c)
			cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
			motion = True

		# draw the text and timestamp on the frame
		cv2.putText(frame, "Motion: {}".format(motion), (10, 20),
			cv2.FONT_HERSHEY_SIMPLEX, 0.5, ((255, 150, 0), (0, 0, 255))[motion], 2)
		cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
			(10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 150, 0), 1)

		# show the frame and record if the user presses a key
		cv2.imshow("Thresh", thresh)
		cv2.imshow("Delta", frameDelta)
		cv2.imshow("Stream", frame)
	key = cv2.waitKey(1) & 0xFF

	# if the `q` key is pressed, break from the lop
	if key == ord("q"):
		break

# cleanup the camera and close any open windows
cv2.destroyAllWindows()