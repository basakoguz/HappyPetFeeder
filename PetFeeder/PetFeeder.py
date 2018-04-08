#!/usr/bin/env python
from flask import Flask, render_template, Response, flash, request, session
from wtforms import Form, SubmitField, Label

# Raspberry Pi camera module (requires picamera package)
from camera_pi import Camera

import time
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders
import os
import sys
import RPi.GPIO as GPIO
import httplib2
import json
import html2text
import picamera


MOTORON = True
LOGFILE = "/tmp/petfeeder.log"
NEWMAIL_OFFSET = 0
lastEmailCheck = time.time()
motorPin = 17
FEEDFILE="/home/pi/latestFeed"
portion = 1
rotateDuration = portion * 0,5
day = "day"
buttonPushed = 0
buttonWait = 300		

app = Flask(__name__)
app.secret_key = "super secret key"


class PetFeederForm(Form):
	FeedNow = SubmitField("FeedNow")
	ConfirmFeeding = SubmitField("ConfirmFeeding")


@app.route('/', methods=['GET', 'POST'])
def index():

    form = PetFeederForm()

    logFile = open(LOGFILE, 'a')

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(motorPin, GPIO.OUT)
    GPIO.output(motorPin, 0)

    global buttonPushed

    if os.path.isfile(FEEDFILE):

        with open(FEEDFILE, 'r') as feedFile:

           latestFeed = float(feedFile.read())
           feedFile.close()

    else:

        latestFeed = time.time()
        savelatestFeed()    


    ldate = time.strftime("%d-%m-%y" , time.localtime(latestFeed))
    ltime = time.strftime("%X" , time.localtime(latestFeed))

    lastFeedDate = {'date': ldate}
    lastFeedTime = {'time': ltime}


    """Video streaming home page."""
    if request.method == 'POST':

	if request.form['submit'] == "Feed Now!":

        	if (time.time() - buttonPushed) < buttonWait:

			flash('You have already fed your pet! Please, wait for at least 5 minutes.')
		
		else:
#			flash('Feeding time for your pet has not come yet!')
#			flash('If you still want to feed, click -Confirm Feeding- button.')
		

#	elif request.form['submit'] == "Confirm Feeding":

			latestFeed = feedNow()
			savelatestFeed(latestFeed)
			buttonPushed = time.time()
			flash('Feeding successful!')
		
	   		ldate = time.strftime("%d-%m-%y" , time.localtime(latestFeed))
    			ltime = time.strftime("%X" , time.localtime(latestFeed))

    			lastFeedDate = {'date': ldate}
    			lastFeedTime = {'time': ltime}


    return render_template('index.html', form=form, lastFeedTime=lastFeedTime, lastFeedDate=lastFeedDate)

def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


def sendEmail(to, subject, text, attach=None):

    msg = MIMEMultipart()
    msg['From'] = 'happypetfeeder00@gmail.com'
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(text))

    if attach:

        part = MIMEBase('application', 'octet-stream')
        part.set_payload(open(attach, 'rb').read())
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(attach))
        msg.attach(part)

    mailServer = smtplib.SMTP("smtp.gmail.com", 587)
    mailServer.ehlo()
    mailServer.starttls()
    mailServer.ehlo()
    mailServer.login('happypetfeeder00@gmail.com', 'corciyatek')
    mailServer.sendmail('happypetfeeder00@gmail.com', to, msg.as_string())
    mailServer.close()

def feedNow():

    global GPIO
    global motorPin
    global latestFeed
    global successfullFeed    

    if MOTORON:
	
        GPIO.output(motorPin, True)
        time.sleep(rotateDuration)
        GPIO.output(motorPin, False)
        sendEmail('happypetfeeder00@gmail.com', "Besleme onayi |  " + time.strftime("Tarih: %d-%m-%y Saat: %X", time.gmtime(time.time())), "Besleme basarili")

        time.sleep(2)

    return time.time()


def savelatestFeed(latestFeed):

    global FEEDFILE
    with open(FEEDFILE, 'w') as feedFile:

        feedFile.write(str(latestFeed))

    feedFile.close()


if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=True, threaded=True)




