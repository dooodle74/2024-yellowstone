from flask import Flask, render_template, request, redirect, url_for
from flask_mail import Mail, Message
import json
import subprocess
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import os
from datetime import datetime

app = Flask(__name__)

CONFIG_EMAIL = ''
CONFIG_PASSWORD = ''
SENDER_EMAIL = ''
SENDER_NAME = 'Yellowstone Lodge Notifications'
RECEPIENTS = []

# Local Env
import os
from dotenv import load_dotenv

load_dotenv()
CONFIG_EMAIL = os.getenv('CONFIG_EMAIL')
CONFIG_PASSWORD = os.getenv('CONFIG_PASSWORD')
SENDER_EMAIL = os.getenv('CONFIG_EMAIL')
i = 0
while True:
    index = f'VAR{i}'
    recepient = os.getenv(index)
    if recepient is None:
        break
    RECEPIENTS.append(recepient)
    i += 1


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = CONFIG_EMAIL 
app.config['MAIL_PASSWORD'] = CONFIG_PASSWORD 
app.config['MAIL_DEFAULT_SENDER'] = (SENDER_NAME, SENDER_EMAIL)

# Initialize Flask-Mail
mail = Mail(app)

def send_email(subject, body, recipient, app):
    with app.app_context():
        try:
            msg = Message(subject, recipients=[recipient])
            msg.body = body
            mail.send(msg)
            print("Email sent successfully.")
        except Exception as e:
            print(f"Error sending email: {e}")

# Function to load JSON data from file
def load_json(filename):
    try:
        with open(filename, 'r') as file:
            data = json.load(file)
            return data, os.path.getmtime(filename)  # Return data and last modified time
    except FileNotFoundError:
        return None, None
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        return None, None

# Function to update JSON data using save_json.py
def update_json():
    try:
        subprocess.run(["python", "save_json.py"])  # Runs the save_json.py script
        print("JSON file updated successfully.")
        return True
    except Exception as e:
        print(f"Error updating JSON file: {e}")
        return False

# Function to fetch value from JSON based on date, category, and guest key
def fetch_value_from_json(data, date_key, category_key, guest_key):
    try:
        if data is None:
            return "Data not loaded"  # Handle case where data is None
        
        if date_key in data["availability"] and \
           category_key in data["availability"][date_key] and \
           "perGuests" in data["availability"][date_key][category_key] and \
           guest_key in data["availability"][date_key][category_key]["perGuests"]:
            return data["availability"][date_key][category_key]["perGuests"][guest_key].get("b", "N/A")
        else:
            return "N/A"
    except Exception as e:
        print(f"Error fetching value from JSON: {e}")
        return "Error"

# Function to check for notifications
def check_notifications():
    
    try:
        # Load JSON data within the function
        filename = "yellowstone_availability.json"
        data, _ = load_json(filename)
        
        if data:
            lodge_values = {
                "YLCL" : "Canyon Lodge",
                "YLGV" : "Grant Village",
                "YLMH" : "Mammoth Hotel",
                "YLLH" : "Lake Yellowstone", 
                "YLLL" : "Lake Lodge Cabins",
                "YLOI" : "Old Faithful Inn",
                "YLOL" : "Old Faithful Lodge",
                "YLOS" : "Old Faithful Snow Lodge",
                "YLRL" : "Roosevelt Lodge"
            }
            
            dates = ["07/11/2024", "07/12/2024", "07/13/2024", "07/14/2024", "07/15/2024"]
            category_keys = list(lodge_values.keys())
            guest_key = "3"

            notify = []
            msg_content = ""
            for date_key in dates:
                for category_key in category_keys:
                    value = fetch_value_from_json(data, date_key, category_key, guest_key)
                    if value != "N/A" and value <= 250:
                        pair = (date_key, category_key, value)
                        notify.append(pair)
                        
            for tup in notify:
                lodge = lodge_values[tup[1]]
                msg_content += f"{lodge} available on {tup[0]} for ${tup[2]}\n"

            if msg_content != "":
                for recipient in RECEPIENTS:
                    send_email(f"Notification: {len(notify)} spots", msg_content, recipient, app)
            else:
                print("No email sent")
        else:
            print("JSON data not loaded.")
            
    except Exception as e:
        print(f"Error checking notifications: {e}")

# Scheduler setup
scheduler = BackgroundScheduler()
scheduler.add_job(func=update_json, trigger="interval", minutes=3)
scheduler.add_job(func=check_notifications, trigger="interval", minutes=5)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

# Route to display table of results and last updated time
@app.route('/')
def index():
    # Filename of the saved JSON data
    filename = "yellowstone_availability.json"
    data, last_updated_time = load_json(filename)
    
    if data:
        # Define dynamic parameters
        guest_key = "3"

        # Dates to display in the table (can be adjusted as needed)
        dates = ["07/11/2024", "07/12/2024", "07/13/2024", "07/14/2024"]
        
        # Fetch values for each date and category
        results_YLRL = []
        results_YLOS = []
        results_YLOL = []
        for date_key in dates:
            # Fetch for category YLRL
            result_YLRL = fetch_value_from_json(data, date_key, "YLRL", guest_key)
            results_YLRL.append(result_YLRL)
            
            # Fetch for category YLOS
            result_YLOS = fetch_value_from_json(data, date_key, "YLOS", guest_key)
            results_YLOS.append(result_YLOS)

            # Fetch for category YLOL
            result_YLOL = fetch_value_from_json(data, date_key, "YLOL", guest_key)
            results_YLOL.append(result_YLOL)
    else:
        results_YLRL = ["Failed to load JSON data"] * len(dates)
        results_YLOS = ["Failed to load JSON data"] * len(dates)
        results_YLOL = ["Failed to load JSON data"] * len(dates)
        last_updated_time = None
    
    # Format last updated time for display
    last_updated_str = datetime.fromtimestamp(last_updated_time).strftime('%Y-%m-%d %H:%M:%S') if last_updated_time else "Unknown"

    return render_template('index.html', results_YLRL=results_YLRL, results_YLOS=results_YLOS, results_YLOL=results_YLOL, dates=dates, last_updated_time=last_updated_str)

# Route to handle manual update request
@app.route('/update', methods=['POST'])
def manual_update():
    update_success = update_json()
    if update_success:
        return redirect(url_for('index', update_status=True))
    else:
        return "Failed to update JSON file."

if __name__ == '__main__':
    with app.app_context():
        app.run(debug=True)
