#!/usr/bin/env python

from imapclient import IMAPClient, SEEN
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

MOTORON = True
NEWMAIL_OFFSET = 0
lastEmailCheck = time.time()
motorPin = 17
feedInterval = 28800
FEEDFILE="/home/pi/latestFeed"
portion = 1
rotateDuration = portion * 0,5
day = "day"

def checkMail():

    global lastEmailCheck
    global latestFeed
    global feedInterval

    if (time.time() > (lastEmailCheck + 40)):

        lastEmailCheck = time.time()
        server = IMAPClient('imap.gmail.com', use_uid=True, ssl=True)
        server.login('happypetfeeder@gmail.com', '*****')
        server.select_folder('Inbox')

        whenMessages = server.search([u'UNSEEN', u'SUBJECT', u'Son'])

        if whenMessages:

            for msg in whenMessages:

                msginfo = server.fetch([msg], ['BODY[HEADER.FIELDS (FROM)]'])
                fromAddress = str(msginfo[msg].get('BODY[HEADER.FIELDS (FROM)]')).split('<')[1].split('>')[0]
                msgBody = "Son besleme " + time.strftime("tarihi %d-%m-%y, saati %X ", time.localtime(latestFeed)) + "\n\nCanavarlarin henuz mamaya ihtiyaclari yok.\n\nBir sonraki besleme " + time.strftime("tarihi %d-%m-%y, saati %X olacak.", time.localtime(latestFeed + feedInterval))

                sendEmail(fromAddress, "En son besleme bilgileri su sekilde", msgBody)

                server.add_flags(whenMessages, [SEEN])

        feedMessages = server.search([u'UNSEEN', u'SUBJECT', u'Besle'])

        if feedMessages:

            for msg in feedMessages:

                msginfo = server.fetch([msg], ['BODY[HEADER.FIELDS (FROM)]'])
                fromAddress = str(msginfo[msg].get('BODY[HEADER.FIELDS (FROM)]')).split('<')[1].split('>')[0]
                msgBody = "Bir onceki besleme " + time.strftime("tarihi %d-%m-%y, saati %X.", time.localtime(latestFeed))
                msgBody = msgBody + "\n\nCanavarlarin henuz mamaya ihtiyaclari yok. \nBir sonraki otomatik besleme " + time.strftime("tarihi %d-%m-%y, saati %X olacak.", time.localtime(latestFeed + feedInterval)) + "\n\nYine de beslemek istiyorsan bu mesaji konu kismina 'Onay' yazarak cevapla."

                sendEmail(fromAddress, "Besleme icin biraz daha beklemelisin", msgBody)

                server.add_flags(feedMessages, [SEEN])

        confirmMessages = server.search ([u'UNSEEN', u'SUBJECT', u'Onay'])

        if confirmMessages:

			for msg in confirmMessages:

				msginfo = server.fetch([msg], ['BODY[HEADER.FIELDS (FROM)]'])
				fromAddress = str(msginfo[msg].get('BODY[HEADER.FIELDS (FROM)]')).split('<')[1].split('>')[0]
				msgBody = "Bir onceki besleme " + time.strftime("tarihi %d-%m-%y, saati %X.", time.localtime(latestFeed)) + "\n\nYeni besleme saati " + time.strftime("%X",time.localtime()) + " olarak kaydedildi." + "\n\nBir sonraki otomatik besleme " + time.strftime("tarihi %d-%m-%y, saati %X olacak.", time.localtime(latestFeed + feedInterval))
				sendEmail(fromAddress, "Mmm mamalar lezizmis!", msgBody)
				server.add_flags(confirmMessages, [SEEN])

			return True

    return False

def sendEmail(to, subject, text, attach=None):

    msg = MIMEMultipart()
    msg['From'] = 'happypetfeeder@gmail.com'
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
    mailServer.login('happypetfeeder@gmail.com', '*****')
    mailServer.sendmail('happypetfeeder@gmail.com', to, msg.as_string())
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
        sendEmail('happypetfeeder@gmail.com', "Besleme onayi |  " + time.strftime("Tarih: %d-%m-%y Saat: %X", time.gmtime(time.time())), "Besleme basarili")

        time.sleep(2)

    return time.time()

def savelatestFeed():

    global FEEDFILE
    global latestFeed
    with open(FEEDFILE, 'w') as feedFile:

        feedFile.write(str(latestFeed))

    feedFile.close()

try:

	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(motorPin, GPIO.OUT)
	GPIO.output(motorPin, 0)

	if os.path.isfile(FEEDFILE):

		with open(FEEDFILE, 'r') as feedFile:

			latestFeed = float(feedFile.read())
			feedFile.close()

	else:

		latestFeed = time.time()
		savelatestFeed()

	while True:

		if (time.time() - latestFeed) > feedInterval:

			latestFeed = feedNow()
			savelatestFeed()

		else:
			if checkMail():
				latestFeed = feedNow()
				savelatestFeed()

		time.sleep(.6)

except KeyboardInterrupt:

	GPIO.cleanup()

except SystemExit:

	GPIO.cleanup()
