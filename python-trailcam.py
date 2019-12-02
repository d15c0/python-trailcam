#!/usr/bin/python3

import io
import time
import picamera
import datetime
import logging
import socketserver
import os
from signal import pause
from threading import Thread
from threading import Condition
from http import server
from datetime import timedelta
from picamera import PiCamera
from gpiozero import Button
import subprocess


button = Button(21)

intf = 'tun0'
intf_ip = subprocess.getoutput("ip address show dev " + intf).split()
intf_ip = intf_ip[intf_ip.index('inet') + 1].split('/')[0]
print(intf_ip)

STARTTIME = time.time() 
STREAM_WIDTH = 640
STREAM_HEIGHT = 480
CAMERA_WIDTH = 3280 # 3280
CAMERA_HEIGHT = 2464 # 2464
EXPOSURE = 'auto'
FRAMERATE = 2

PAGE="""\
<html>
<head>
<title>*** Live Camera ***</title>
</head>
<body>
<h1>Live Camera {intf_ip}</h1>
<img src="stream.mjpg" width=STREAM_WIDTH height=STREAM_HEIGHT />
</body>
</html>
""".format(**locals()) #this allows variables to be used in the html code...


class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

with picamera.PiCamera() as camera:
    camera.resolution = (CAMERA_WIDTH, CAMERA_HEIGHT)
    camera.framerate = FRAMERATE
    camera.exposure_mode = EXPOSURE # exposure modes
    camera.shutter_speed = 10000 # in micro-seconds 
    output = StreamingOutput()
    camera.start_recording(output, format='mjpeg')
    server = StreamingServer(('0.0.0.0', <whatever>), StreamingHandler)
    server_thread = Thread(target=server.serve_forever)
    output = StreamingOutput()
    camera.start_recording(output, format='mjpeg', splitter_port=2, resize=(STREAM_WIDTH, STREAM_HEIGHT))
    
    def capturePhoto():
        while button.is_pressed:
            datetimeNow = datetime.datetime.now()
            datetimeNowStr = datetimeNow.strftime("%Y-%m-%d %H-%M-%S")
            camera.annotate_text = datetimeNowStr
            time.sleep(2.0 - ((time.time() - STARTTIME) % 2.0))
            camera.capture(datetimeNowStr + '.jpg', use_video_port=True)

    try:
        server_thread.start()
        
        if button.is_pressed:
            capturePhoto()

        while True:
            button.when_pressed = capturePhoto
            pause()
    
    finally :
        camera.stop_recording()
