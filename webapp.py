from flask import Flask, render_template, request, redirect, url_for, session, send_file
from bson import ObjectId
from telegram import Bot
import pymongo
import os
import random
import string

app = Flask(__name__)

# Connect to MongoDB
try:
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client["fire_detection_db"]
except Exception as e:
    print("Error connecting to MongoDB:", e)

# Generate a random string of characters for the secret key
secret_key = os.urandom(24)

# Set the secret key for the Flask application
app.secret_key = secret_key

# Create a unique index on the device_id field in the users collection
try:
    db.users.create_index("device_id", unique=True)
    print("Unique index created successfully on device_id field.")
except pymongo.errors.OperationFailure as e:
    print("Error creating unique index:", e)

# Function to send a message via Telegram
def send_telegram_message(chat_id, message):
    try:
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')  # Get bot token from environment variable
        if not bot_token:
            print("Telegram bot token not found. Please set the TELEGRAM_BOT_TOKEN environment variable.")
            return False

        bot = Bot(token=bot_token)
        bot.send_message(chat_id=chat_id, text=message)
        return True
    except Exception as e:
        print("Error sending Telegram message:", e)
        return False

# Route to serve the index.html file
@app.route('/')
def index():
    # Return the index.html file located in the static folder
     return render_template('index.html')
# Handle form submission to add a new user
@app.route('/add_user', methods=['POST'])
def add_user():
    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        place = request.form['place']
        phoneNo = request.form['phoneNo']
        device_id = request.form['device_id']
        
        # Generate a random password
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))  # Increased password length
        
        try:
            users_collection = db["users"]
            
            # Check if the email already exists
            if users_collection.find_one({"email": email}):
                return "Email already exists"
            
            # Check if the device_id already exists
            if users_collection.find_one({"device_id": device_id}):
                return "Device ID already exists"
            
            # Insert new user
            new_user = {
                "firstname": firstname,
                "lastname": lastname,
                "email": email,
                "place": place,
                "phoneNo": phoneNo,
                "device_id": device_id,
                "password": password
            }
            result = users_collection.insert_one(new_user)
            
            # Get the inserted user document
            inserted_user = users_collection.find_one({"_id": result.inserted_id})
            
            # Convert ObjectId to string before storing in session
            inserted_user['_id'] = str(inserted_user['_id'])
            
            # Set the user session
            session['user'] = inserted_user
            
            # Send password to user via Telegram
            if not send_telegram_message(chat_id=phoneNo, message=f'Your password: {password}'):
                return "Failed to send Telegram message. User added, but password not sent."
            
            return redirect(url_for('user_profile'))
        
        except pymongo.errors.DuplicateKeyError:
            return "Email or Device ID already exists"  # Handle duplicate key error
        
        except Exception as e:
            return "An error occurred while adding the user: {}".format(e)
        
    return "Method not allowed"

# Route for the user profile page
@app.route('/user_profile')
def user_profile():
    # Check if user is logged in
    if 'user' in session:
        user = session['user']
        # Render the user profile page with user data
        return render_template('user_profile.html', user=user)
    else:
        # If user is not logged in, redirect to the sign-in page
        return redirect(url_for('login'))

# Route for logging in
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Check if user exists in the database
        user = db.users.find_one({'email': email, 'password': password})
        
        if user:
            # Convert ObjectId to string before storing in session
            user['_id'] = str(user['_id'])
            
            # Set the user session
            session['user'] = user
            return redirect(url_for('user_profile'))
        else:
            # User not found, redirect back to sign-in page with error message
            return render_template('login.html', error='Invalid email or password')
    else:
        return render_template('login.html')

# Route for logging out
@app.route('/logout', methods=['GET'])
def logout():
    # Clear the session data
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
