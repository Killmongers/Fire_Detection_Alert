import cv2
import threading
import pygame
import math
import cvzone
from ultralytics import YOLO
from datetime import datetime
from pymongo import MongoClient
import tkinter as tk

# Initialize Pygame for playing sound
pygame.init()
pygame.mixer.init()

# Load the YOLO model for fire detection
model = YOLO('best.pt')

# Reading the classes
classnames = ['fire', 'smoke']

# Initialize variables
alarm_playing = False

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['fire_detection_db']
collection = db['Log']
users_collection = db['users']

# Function to play alarm sound
def play_alarm_sound_function():
    global alarm_playing
    alarm_playing = True
    pygame.mixer.music.load('fire_alarm.mp3')  # Update with your fire alarm sound file path
    pygame.mixer.music.play()
    print("Fire alarm playing")

# Function to get the list of device_id from the database
def get_device_id_list():
    device_id_list = []
    cursor = users_collection.find({}, {"device_id": 1})
    for document in cursor:
        device_id_list.append(document.get("device_id"))
    return device_id_list

# Function to capture data from the GUI interface
def get_admin_input():
    root = tk.Tk()
    root.title("Admin Interface")

    place_label = tk.Label(root, text="Place:")
    place_label.grid(row=0, column=0, padx=10, pady=5)
    place_entry = tk.Entry(root)
    place_entry.grid(row=0, column=1, padx=10, pady=5)

    email_id_label = tk.Label(root, text="email_id:")
    email_id_label.grid(row=1, column=0, padx=10, pady=5)
    email_id_entry = tk.Entry(root)
    email_id_entry.grid(row=1, column=1, padx=10, pady=5)

    # Create the device ID dropdown menu
    device_id_label = tk.Label(root, text="Select Device ID:")
    device_id_label.grid(row=2, column=0, padx=10, pady=5)
    device_id_list = get_device_id_list()
    device_id_var = tk.StringVar(root)
    device_id_dropdown = tk.OptionMenu(root, device_id_var, *device_id_list)
    device_id_dropdown.grid(row=2, column=1, padx=10, pady=5)

    def submit_data():
        place = place_entry.get()
        email_id = email_id_entry.get()
        device_id = device_id_var.get()
        # Check if email ID, device ID, and place combination already exists
        if users_collection.find_one({"email_id": email_id, "device_id": device_id, "place": place}):
           error_label.config(text="Combination of email ID, device ID, and place already exists", fg="red")
           return
        

    

        # Call the video processing function with the collected data
        if place and email_id and device_id:
            process_video(place, email_id, device_id)
            root.destroy()
        else:
            error_label.config(text="Please fill in all fields", fg="red")

    submit_button = tk.Button(root, text="Submit", command=submit_data)
    submit_button.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

    error_label = tk.Label(root, text="", fg="red")
    error_label.grid(row=4, column=0, columnspan=2)

    root.mainloop()

# Function to process video
def process_video(place, email_id, device_id):
    vid = cv2.VideoCapture(0)

    while True:
        ret, frame = vid.read()
        frame = cv2.resize(frame, (640, 480))
        if not ret:
            print("Error reading frame")
            break

        result = model(frame, stream=True)

        for info in result:
            boxes = info.boxes
            for box in boxes:
                confidence = box.conf[0]
                confidence = math.ceil(confidence * 100)
                Class = int(box.cls[0])
                if confidence > 50:
                    x1, y1, x2, y2 = box.xyxy[0]
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 5)
                    cvzone.putTextRect(frame, f'{classnames[Class]} {confidence}%', [x1 + 8, y1 + 100],
                                       scale=1.5, thickness=2)
                    if not alarm_playing:
                        threading.Thread(target=play_alarm_sound_function).start()
                    
                    # Log detection event to MongoDB
                    log_data = {
                        'timestamp': datetime.now(),
                        'place': place,
                        'email_id': email_id,
                        'device_id': device_id 
                    }
                    collection.insert_one(log_data)

        cv2.imshow('frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    vid.release()
    pygame.mixer.quit()

# Entry point of the program
if __name__ == '__main__':
    # Capture data from the GUI interface
    get_admin_input()
