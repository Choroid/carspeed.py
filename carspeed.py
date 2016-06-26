# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import datetime
import cv2
from functions import *
from constants import *

print("Image width in feet {} at {} from camera".format("%.0f" % frame_width_ft, "%.0f" % DISTANCE))

# initialize the camera 
camera = PiCamera()
camera.resolution = RESOLUTION
camera.framerate = FPS
camera.vflip = False
camera.hflip = False

rawCapture = PiRGBArray(camera, size=camera.resolution)
# allow the camera to warm up
time.sleep(0.9)

# create an image window and place it in the upper left corner of the screen
cv2.namedWindow("Speed Camera")
cv2.moveWindow("Speed Camera", 10, 40)

# call the draw_rectangle routines when the mouse is used
cv2.setMouseCallback('Speed Camera', draw_rectangle)
 
# grab a reference image to use for drawing the monitored area's boundary
camera.capture(rawCapture, format="bgr", use_video_port=True)
image = rawCapture.array
rawCapture.truncate(0)
org_image = image.copy()

prompt = "Define the monitored area - press 'c' to continue" 
prompt_on_image(prompt)
 
# wait while the user draws the monitored area's boundary
while not setup_complete:
    cv2.imshow("Speed Camera", image)
 
    # wait for for c to be pressed
    key = cv2.waitKey(1) & 0xFF
  
    # if the `c` key is pressed, break from the loop
    if key == ord("c"):
        break
    
# call the draw_rectangle routines when the mouse is used
cv2.setMouseCallback('Speed Camera', draw_line)

prompt = "Define the frame scale - press 'c' to continue" 
prompt_on_image(prompt)
 
# wait while the user draws the monitored area's boundary
while not setup_complete:
    cv2.imshow("Speed Camera", image)
 
    # wait for for c to be pressed
    key = cv2.waitKey(1) & 0xFF
  
    # if the `c` key is pressed, break from the loop
    if key == ord("c"):
        break

# the monitored area is defined, time to move on
prompt = "Press 'q' to quit" 
 
# since the monitored area's bounding box could be drawn starting 
# from any corner, normalize the coordinates
 
if fx > ix:
    upper_left_x = ix
    lower_right_x = fx
else:
    upper_left_x = fx
    lower_right_x = ix
 
if fy > iy:
    upper_left_y = iy
    lower_right_y = fy
else:
    upper_left_y = fy
    lower_right_y = iy
     
monitored_width = lower_right_x - upper_left_x
monitored_height = lower_right_y - upper_left_y
 
print("Monitored area:")
print(" upper_left_x {}".format(upper_left_x))
print(" upper_left_y {}".format(upper_left_y))
print(" lower_right_x {}".format(lower_right_x))
print(" lower_right_y {}".format(lower_right_y))
print(" monitored_width {}".format(monitored_width))
print(" monitored_height {}".format(monitored_height))
print(" monitored_area {}".format(monitored_width * monitored_height))
 
# capture frames from the camera (using capture_continuous.
#   This keeps the picamera in capture mode - it doesn't need
#   to prep for each frame's capture.

for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    # initialize the timestamp
    timestamp = datetime.datetime.now()
 
    # grab the raw NumPy array representing the image 
    image = frame.array
 
    # crop the frame to the monitored area, convert it to grayscale, and blur it
    # crop area defined by [y1:y2,x1:x2]
    gray = image[upper_left_y:lower_right_y, upper_left_x:lower_right_x]
 
    # convert it to grayscale, and blur it
    gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, BLURSIZE, 0)
 
    # if the base image has not been defined, initialize it
    if base_image is None:
        base_image = gray.copy().astype("float")
        lastTime = timestamp
        rawCapture.truncate(0)
        cv2.imshow("Speed Camera", image)
        continue
 
    # compute the absolute difference between the current image and
    # base image and then turn everything lighter than THRESHOLD into
    # white
    frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(base_image))
    thresh = cv2.threshold(frameDelta, THRESHOLD, 255, cv2.THRESH_BINARY)[1]
  
    # dilate the thresholded image to fill in any holes, then find contours
    # on thresholded image
    thresh = cv2.dilate(thresh, None, iterations=2)
    (_, cnts, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # look for motion 
    motion_found = False
    biggest_area = 0
 
    # examine the contours, looking for the largest one
    for c in cnts:
        (x, y, w, h) = cv2.boundingRect(c)
        # get an approximate area of the contour
        found_area = w*h 
        # find the largest bounding rectangle
        if (found_area > MIN_AREA) and (found_area > biggest_area):  
            biggest_area = found_area
            motion_found = True

    if motion_found:
        if state == WAITING:
            # initialize tracking
            state = TRACKING
            initial_x = x
            last_x = x
            initial_time = timestamp
            last_mph = 0
            text_on_image = 'Tracking'
            print(text_on_image)
        else:

            if state == TRACKING:       
                if x >= last_x:
                    direction = LEFT_TO_RIGHT
                    abs_chg = x + w - initial_x
                else:
                    direction = RIGHT_TO_LEFT
                    abs_chg = initial_x - x
                secs = secs_diff(timestamp, initial_time)
                mph = get_speed(abs_chg, ftperpixel, secs)
                print("--> chg={}  secs={}  mph={} this_x={} w={} ".format(abs_chg, secs, "%.0f" % mph, x, w))
                real_y = upper_left_y + y
                real_x = upper_left_x + x
                # is front of object outside the monitored boundary? Then write date, time and speed on image
                # and save it 
                if ((x <= 2) and (direction == RIGHT_TO_LEFT)) \
                        or ((x+w >= monitored_width - 2) and (direction == LEFT_TO_RIGHT)):
                    # timestamp the image
                    cv2.putText(image, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
                                (10, image.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 1)
                    # write the speed: first get the size of the text
                    size, base = cv2.getTextSize("%.0f mph" % last_mph, cv2.FONT_HERSHEY_SIMPLEX, 2, 3)
                    # then center it horizontally on the image
                    cntr_x = int((IMAGEWIDTH - size[0]) / 2) 
                    cv2.putText(image, "%.0f mph" % last_mph,
                                (cntr_x, int(IMAGEHEIGHT * 0.2)), cv2.FONT_HERSHEY_SIMPLEX, 2.00, (0, 255, 0), 3)
                    # and save the image to disk
                    cv2.imwrite("car_at_"+datetime.datetime.now().strftime("%Y%m%d_%H%M%S")+".jpg",
                                image)
                    state = SAVING
                # if the object hasn't reached the end of the monitored area, just remember the speed 
                # and its last position
                last_mph = mph
                last_x = x
    else:
        if state != WAITING:
            state = WAITING
            direction = UNKNOWN
            text_on_image = 'No Car Detected'
            print(text_on_image)
            
    # only update image and wait for a keypress when waiting for a car
    # or if 50 frames have been processed in the WAITING state.
    # This is required since waitkey slows processing.
    if (state == WAITING) or (loop_count > 50):    
 
        # draw the text and timestamp on the frame
        cv2.putText(image, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
                    (10, image.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 1)
        cv2.putText(image, "Road Status: {}".format(text_on_image), (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
     
        if show_bounds:
            # define the monitored area right and left boundary
            cv2.line(image, (upper_left_x, upper_left_y), (upper_left_x, lower_right_y), (0, 255, 0))
            cv2.line(image, (lower_right_x, upper_left_y), (lower_right_x, lower_right_y), (0, 255, 0))
       
        # show the frame and check for a keypress
        if showImage:
            prompt_on_image(prompt)
            cv2.imshow("Speed Camera", image)
        if state == WAITING:
            last_x = 0
            cv2.accumulateWeighted(gray, base_image, 0.25)
 
        state = WAITING
        key = cv2.waitKey(1) & 0xFF
      
        # if the `q` key is pressed, break from the loop and terminate processing
        if key == ord("q"):
            break
        loop_count = 0
         
    # clear the stream in preparation for the next frame
    rawCapture.truncate(0)
    loop_count += 1
  
# cleanup the camera and close any open windows
cv2.destroyAllWindows()
