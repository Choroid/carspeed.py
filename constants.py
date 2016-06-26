import math

# define some constants
DISTANCE = 20  # <---- enter your distance-to-road value here
THRESHOLD = 15
MIN_AREA = 175
BLURSIZE = (15, 15)
IMAGEWIDTH = 640
IMAGEHEIGHT = 480
RESOLUTION = [IMAGEWIDTH, IMAGEHEIGHT]
FOV = 53.5
FPS = 30
VFLIP = False
HFLIP = False

# the following enumerated values are used to make the program more readable
WAITING = 0
TRACKING = 1
SAVING = 2
UNKNOWN = 0
LEFT_TO_RIGHT = 1
RIGHT_TO_LEFT = 2

# calculate the the width of the image at the distance specified
frame_width_ft = 2*(math.tan(math.radians(FOV*0.5))*DISTANCE)
ftperpixel = frame_width_ft / float(IMAGEWIDTH)

# state maintains the state of the speed computation process
# if starts as WAITING
# the first motion detected sets it to TRACKING

# if it is tracking and no motion is found or the x value moves
# out of bounds, state is set to SAVING and the speed of the object
# is calculated
# initial_x holds the x value when motion was first detected
# last_x holds the last x value before tracking was was halted
# depending upon the direction of travel, the front of the
# vehicle is either at x, or at x+w
# (tracking_end_time - tracking_start_time) is the elapsed time
# from these the speed is calculated and displayed

state = WAITING
direction = UNKNOWN
initial_x = 0
last_x = 0

# -- other values used in program
base_image = None
abs_chg = 0
mph = 0
secs = 0.0
show_bounds = True
showImage = True
ix, iy = -1, -1
fx, fy = -1, -1
drawing = False
setup_complete = False
tracking = False
text_on_image = 'No cars'
loop_count = 0