from flask import Flask, render_template, request
from bson import ObjectId
import pymongo

app = Flask(__name__)

# Connect to MongoDB
try:
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client["fire_detection_db"]
except Exception as e:
    print("Error connecting to MongoDB:", e)

# Create a unique index on the device_id field in the user_detail collection
try:
    db.user_detail.create_index("device_id", unique=True)
    print("Unique index created successfully on device_id field.")
except pymongo.errors.OperationFailure as e:
    print("Error creating unique index:", e)

@app.route('/')
def index():
    return render_template('index.html')

# Render the form for adding a new device
@app.route('/add_device_form')
def add_device_form():
    return render_template('add_device_form.html')

# Handle form submission to add a new device
@app.route('/add_device', methods=['POST'])
def add_device_route():
    device_name = request.form['device_name']
    result = add_device(device_name)
    return result

# Function to add a new device
def add_device(device_name):
    try:
        devices_collection = db["devices"]
        
        # Check if the device name already exists
        if devices_collection.find_one({"device_name": device_name}):
            return "Device name already exists"
        
        # Insert new device with auto-generated _id
        new_device = {"device_name": device_name}
        result = devices_collection.insert_one(new_device)
        
        # Retrieve the auto-generated _id
        device_id = result.inserted_id
        
        # Update the document to include a separate device_id
        devices_collection.update_one({"_id": device_id}, {"$set": {"device_id": str(device_id)}})
        
        return "Device added successfully with ID: {}".format(device_id)
    except Exception as e:
        return "An error occurred while adding the device: {}".format(e)

# Render the form for adding a new user
@app.route('/add_user_form')
def add_user_form():
    device_ids = get_device_ids()
    return render_template('add_user_form.html', device_ids=device_ids)

# Function to retrieve device IDs from MongoDB
def get_device_ids():
    try:
        devices_collection = db["devices"]
        device_ids = [str(device["_id"]) for device in devices_collection.find({}, {"_id": 1})]
        return device_ids
    except Exception as e:
        print("Error retrieving device IDs:", e)
        return []

# Handle form submission to add a new user
@app.route('/add_user', methods=['POST'])
def add_user_route():
    username = request.form['username']
    device_id = request.form['device_id']
    result = add_user(username, device_id)
    return result

# Function to add a new user and assign a device
def add_user(username, device_id):
    try:
        db.user_detail.create_index("device_id", unique=True)  
        users_collection = db["user_detail"]
        
        # Check if the device exists
        if not db["devices"].find_one({"_id": ObjectId(device_id)}):
            return "Device ID doesn't exist"
        
        # Check if the username already exists
        if users_collection.find_one({"username": username}):
            return "Username already exists"
        
        # Insert new user
        users_collection.insert_one({"username": username, "device_id": device_id})
        return "User added successfully"
    except Exception as e:
        if 'E11000' in str(e):
            return "Device ID already exists"
        return "An error occurred while adding the user: {}".format(e)

if __name__ == '__main__':
    app.run(debug=True)
