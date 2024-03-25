import cv2
import threading
import smtplib
import math
import cvzone
from ultralytics import YOLO
from playsound import playsound

# Load the YOLO model for fire detection
model = YOLO('best.pt')

# Reading the classes
classnames = ['fire', 'smoke']

# Initialize variables
alarm_playing = False

# Function to play alarm sound
def play_alarm_sound_function():
    global alarm_playing
    alarm_playing = True
    playsound('C:\\Users\\mooly\\Downloads\\Fire_Detection_Alert-main\\fire_alarm.mp3')
    print("Fire alarm end")

# Function to send email
def send_mail_function():
    recipientmail = "add recipients mail"
    recipientmail = recipientmail.lower()
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login("add senders mail", 'add senders password')
        server.sendmail('add senders mail', recipientmail, "Warning fire accident has been reported")
        print("Alert mail sent successfully to {}".format(recipientmail))
        server.close()
    except Exception as e:
        print(e)

# Start video capture
vid = cv2.VideoCapture(0)

while True:
    ret, frame = vid.read()
    frame = cv2.resize(frame, (640, 480))
    if not ret:
        print("Error reading frame")
        break

    result = model(frame, stream=True)

    # Getting bbox, confidence, and class names information to work with
    for info in result:
        boxes = info.boxes
        for box in boxes:
            confidence = box.conf[0]
            confidence = math.ceil(confidence * 100)
            Class = int(box.cls[0])
            if confidence > 70:
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 5)
                cvzone.putTextRect(frame, f'{classnames[Class]} {confidence}%', [x1 + 8, y1 + 100],
                                   scale=1.5, thickness=2)
                if not alarm_playing:
                    threading.Thread(target=play_alarm_sound_function).start()

    cv2.imshow('frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release video capture
vid.release()
