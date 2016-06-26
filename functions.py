from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import math
import datetime
import cv2
from constants import *

# place a prompt on the displayed image
def prompt_on_image(txt):
    global image
    cv2.putText(image, txt, (10, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)


# calculate speed from pixels and time
def get_speed(pixels, ftperpixel, secs):
    if secs > 0.0:
        return ((pixels * ftperpixel) / secs) * 0.681818  # fps to mph
    else:
        return 0.0


# calculate elapsed seconds
def secs_diff(endTime, begTime):
    diff = (endTime - begTime).total_seconds()
    return diff


# mouse callback function for drawing scale
def draw_line(event, x, y):
    global ix, iy, fx, fy, drawing, setup_complete, image, org_image, prompt

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            image = org_image.copy()
            prompt_on_image(prompt)
            cv2.line(image, (ix, iy), (x, y), (0, 255, 0), 2)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        fx, fy = x, y
        image = org_image.copy()
        prompt_on_image(prompt)
        cv2.line(image, (ix, iy), (fx, fy), (0, 255, 0), 2)


# mouse callback function for drawing capture area
def draw_rectangle(event, x, y):
    global ix, iy, fx, fy, drawing, setup_complete, image, org_image, prompt

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            image = org_image.copy()
            prompt_on_image(prompt)
            cv2.rectangle(image, (ix, iy), (x, y), (0, 255, 0), 2)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        fx, fy = x, y
        image = org_image.copy()
        prompt_on_image(prompt)
        cv2.rectangle(image, (ix, iy), (fx, fy), (0, 255, 0), 2)
