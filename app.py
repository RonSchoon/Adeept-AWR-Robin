#!/usr/bin/env python
# 20250930, RS: Replaced ccamera capture by CV2 with Picamera2
from flask import Flask, render_template, Response, request, jsonify
from flask_httpauth import HTTPDigestAuth
from picamera2 import Picamera2
import cv2, numpy # real-time computer vision
import move
import info
import servo
import functions
import robotLight
import os
import power
import ultra
# needed for wifi check
from subprocess import check_output 
import threading
import time
import json

# Video capturing and detection
face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")	# load haar cascade object to detect faces in a video 
smile_cascade = cv2.CascadeClassifier("haarcascade_smile.xml")
camera = Picamera2()
camera.configure(camera.create_video_configuration(
	main={"size": (320, 240)},
	controls={"FrameDurationLimits": (33333, 33333)}
)) # framerate fixed to 30 frames/s
camera.start()
watchDog = False
detectFaces = False
previous_frame = None
prepared_frame = None

datasets = 'datasets'

# Part 1: Create fisherRecognizer
print('Recognizing Face Please Be in sufficient Lights...')

# Create a list of images and a list of corresponding names
(images, labels, names, id) = ([], [], {}, 0)
for (subdirs, dirs, files) in os.walk(datasets):
	for subdir in dirs:
		names[id] = subdir
		subjectpath = os.path.join(datasets, subdir)
		for filename in os.listdir(subjectpath):
			path = subjectpath + '/' + filename
			label = id
			images.append(cv2.imread(path, 0))
			labels.append(int(label))
		id += 1
(width, height) = (130, 100)

# Create a Numpy array from the two lists above
(images, labels) = [numpy.array(lis) for lis in [images, labels]]

# OpenCV trains a model from the images
# NOTE FOR OpenCV2: remove '.face'
model = cv2.face.LBPHFaceRecognizer_create()
model.train(images, labels)

def checkWiFi():
  threading.Timer(300.0, checkWiFi).start() # Check every 5 min
  # print('Checking WiFi')
  output = check_output(["iwgetid", "--raw"])
  if len(output) < 10:
    RL.setColor(0,255,64)
    os.system("sudo create_ap wlan0 eth0 Robin")
    # print('Try to reconnect to WiFi...')
    # os.system("sudo ifconfig wlan0 down")
    # sleep(2)
    # os.system("sudo ifconfig wlan0 up")
  else:
      print('Connected to {}'.format(output)) # "Connected to b'De Bongerd 69\n'"

# Initializing motor
move.setup()
direction_command = 'no'
turn_command = 'no'
speed_set = 100
rad = 0.5

fuc = functions.Functions()
fuc.start()
power.low()

# Video streaming generator function.
def gen_frames():
	global watchDog, detectFaces
	while True:
		frame = camera.capture_array()	# capture video frame from second read() parameter
		if watchDog:
			frame = detectMotion(frame)
		elif detectFaces:
			frame = detectFaces(frame)	# add detected faces to frame
		jpeg = cv2.imencode('.jpg', frame)[1].tobytes()	# convert frame to jpg
		yield b'--frame\r\n' + b'Content-Type: image/jpeg\r\n\r\n' + jpeg + b'\r\n'
	camera.close()
	yield b'--frame\r\n'

def detectFaces(frame):
	text=""	# Set the default text
	grayImg = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)	# use grayscale format to reduce processing
	faces = face_cascade.detectMultiScale(grayImg,1.3,4)	# detect faces
	for (x,y,w,h) in faces:
		text="Face Detected"
		cv2.rectangle(frame,(x,y),(x+w,y+h), (0,255,0),2)
		# Try to recognize the face
		prediction = model.predict(grayImg)
		if prediction[1]<500:
			cv2.putText(frame, '% s - %.0f' %
			(names[prediction[0]], prediction[1]), (x-10, y-10),
			cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0))
		else:
			cv2.putText(frame, 'not recognized',
			(x-10, y-10), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0))
	if text == "Face Detected":
		print(text)
		RL.setColor(0,255,0)
	else:
		RL.setColor(0,0,0)
	frame = cv2.putText(frame, text, (50,50), cv2.FONT_HERSHEY_SIMPLEX,1, (0,255,0), 2, cv2.LINE_AA)
	return frame

def detectMotion(frame):
	global previous_frame, prepared_frame, camX, watchDog, turn_command
	previous_frame = prepared_frame
	img_rgb = cv2.cvtColor(src=frame, code=cv2.COLOR_BGR2RGB)
	prepared_frame = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
	prepared_frame = cv2.GaussianBlur(src=prepared_frame, ksize=(5, 5), sigmaX=0)
	if (previous_frame is None):
		return frame
	diff_frame = cv2.absdiff(src1=previous_frame, src2=prepared_frame)
	diff_frame = cv2.dilate(diff_frame, numpy.ones((5, 5)), 1)
	thresh_frame = cv2.threshold(src=diff_frame, thresh=20, maxval=255, type=cv2.THRESH_BINARY)[1]
	# Explanation: By using [-2:], we are basically taking the last two values from the tuple returned by cv2.findContours.
	# Since in some versions, it returns (image, contours, hierarchy) and in other versions, it returns (contours, hierarchy), contours, hierarchy are always the last two values.
	contours, hierarchy = cv2.findContours(thresh_frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2:]
	if (contours):
		print("Motion detected! Number of movements found = " + str(len(contours)))
		RL.setColor(255,0,0)
	else:
		RL.setColor(0,0,0)
	# frame = cv2.drawContours(image=frame, contours=contours, contourIdx=-1, color=(0, 255, 0), thickness=2, lineType=cv2.LINE_AA)
	for contour in contours:
		if cv2.contourArea(contour) < 50: # too small: skip!
			continue
		(x, y, w, h) = cv2.boundingRect(contour)
		cv2.rectangle(img=frame, pt1=(x, y), pt2=(x + w, y + h), color=(0, 255, 0), thickness=2)
		objMid = x + (w/2)
		if objMid < 50:
			print("Go left", objMid)
		elif objMid > camX-50:
			print("Go right", objMid)
	return frame

# Initializing the flask object
app = Flask(__name__)

# See: https://flask-httpauth.readthedocs.io/en/latest/
app.config['SECRET_KEY'] = 'secret key here'
auth = HTTPDigestAuth()

@auth.get_password
def get_pw(username):
  # users = {"admin": "password", "gast": "byefaDFaDFASDF"}
  # with open("cr.json", "w") as outfile:
  #   json.dump(users, outfile)
  # numpy.savetxt('cr.out', users, delimiter=',')
  with open('cr.json', 'r') as openfile:
    users = json.load(openfile)
  if username in users:
    return users.get(username)
  return None

@app.route('/', methods=["GET", "POST"])	# Video streaming home page.
@auth.login_required
def index():
    global direction_command, turn_command, watchDog, detectFaces
    if request.method == "POST":
        command_input = request.form.get('action', 'nothing')
        print('Action:', command_input)
        if 'color' == command_input:
            print("color:")
            hexColor = request.form.get('params', 'nothing')
            print(hexColor)
            r = int(hexColor[1:3], 16)
            g = int(hexColor[3:5], 16)
            b = int(hexColor[5:7], 16)
            RL.setColor(r,g,b)
            return 'Color!'
        if 'green' == command_input:
            RL.setSomeColor(0,255,0,[0,1,2])
            return 'Green!'
        elif 'policeOff' == command_input:
            RL.pause()
        elif 'camUp' == command_input:
            servo.camera_ang('lookup','no')
            return 'Camera up'
        elif 'camDown' == command_input:
            servo.camera_ang('lookdown','no')
            return 'Camera down'
        elif 'forward' == command_input:
            direction_command = 'forward'
            move.move(speed_set, 'forward', 'no', rad)
            return 'Moving forward'
        elif 'backward' == command_input:
            direction_command = 'backward'
            move.move(speed_set, 'backward', 'no', rad)
            return 'Moving backward' 
        elif 'DS' == command_input:
            direction_command = 'no'
            move.move(speed_set, 'no', 'no', rad)
            return 'Stop moving'
        elif 'left' == command_input:
            turn_command = 'left'
            move.move(speed_set, 'no', 'left', rad)
            return 'Turn left'
        elif 'right' == command_input:
            turn_command = 'right'
            move.move(speed_set, 'no', 'right', rad)
            return 'Turn right'
        elif 'TS' == command_input:
            turn_command = 'no'
            if direction_command == 'no':
               move.move(speed_set, 'no', 'no', rad)
            else:
              move.move(speed_set, direction_command, 'no', rad)
            return 'Stop turning'
        if 'police' == command_input:
            print('Police')
            RL.police()
            return 'Police'
        elif 'policeOff' == command_input:
            RL.pause()
            return 'Lights off'
        elif 'watchdog' == command_input:
            watchDog = True
            return 'Watchdog on'
        elif 'watchdogOff' == command_input:
            watchDog = False
            return 'Watchdog off'
        elif 'detectFaces' == command_input:
            detectFaces = True
            return 'detectFaces on'
        elif 'detectFacesOff' == command_input:
            detectFaces = False
            return 'detectFaces off'
        elif 'autopilot' == command_input:
            fuc.automatic()
            return 'Autopilot'
        elif 'autopilotOff' == command_input:
            fuc.pause()
            move.motorStop()
            return 'Autopilot off'
        elif 'powerLow' == command_input:
            power.low()
            return 'power low'
        elif 'powerDefault' == command_input:
            power.default()
            return 'power default'
        elif 'info' == command_input:
            systemInfo = 'CPU Temp: {}, CPU Use: {} RAM Use: {}'.format(info.get_cpu_tempfunc(), info.get_cpu_use(), info.get_ram_info())
            print(systemInfo)
            return systemInfo
        return command_input
    return render_template('index.html', username=format(auth.current_user()))

@app.route('/video_feed')
def video_feed():
	# Video streaming route. Put this in the src attribute of an img tag.
	return Response(gen_frames(),
		mimetype='multipart/x-mixed-replace; boundary=frame')

RL=robotLight.RobotLight()
RL.start()
RL.breath(70,70,255)

if __name__ == '__main__':
  try:
    RL.pause()
    # RL.setColor(0,255,64)
    RL.setColor(0,0,0)
    print('Started up!')
    checkWiFi()
    app.run(host='0.0.0.0', threaded=True)
  except Exception as e:
    print(e)
    RL.setColor(0,0,0)
    move.destroy()
    camera.close()
