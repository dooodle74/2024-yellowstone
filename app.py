from flask import Flask, render_template
import json
import subprocess
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import os
from datetime import datetime

app = Flask(__name__)

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
def check_notifications(data):
    try:
        dates = ["07/11/2024", "07/12/2024", "07/13/2024", "07/14/2024"]
        category_keys = ["YLRL", "YLOS"]
        guest_key = "3"
        
        for date_key in dates:
            for category_key in category_keys:
                value = fetch_value_from_json(data, date_key, category_key, guest_key)
                if value != "N/A":
                    print(f"Notification: Value {value} found for Date {date_key}, Category {category_key}.")
                    # Here you can implement your actual notification mechanism (e.g., send email, push notification)
    except Exception as e:
        print(f"Error checking notifications: {e}")

# Scheduler setup
scheduler = BackgroundScheduler()
scheduler.add_job(func=update_json, trigger="interval", minutes=1)
scheduler.add_job(func=check_notifications, args=(None,), trigger="interval", minutes=10)  # Pass None as argument for now
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
        for date_key in dates:
            # Fetch for category YLRL
            result_YLRL = fetch_value_from_json(data, date_key, "YLRL", guest_key)
            results_YLRL.append(result_YLRL)
            
            # Fetch for category YLOS
            result_YLOS = fetch_value_from_json(data, date_key, "YLOS", guest_key)
            results_YLOS.append(result_YLOS)
    else:
        results_YLRL = ["Failed to load JSON data"] * len(dates)
        results_YLOS = ["Failed to load JSON data"] * len(dates)
        last_updated_time = None
    
    # Format last updated time for display
    last_updated_str = datetime.fromtimestamp(last_updated_time).strftime('%Y-%m-%d %H:%M:%S') if last_updated_time else "Unknown"

    return render_template('index.html', results_YLRL=results_YLRL, results_YLOS=results_YLOS, dates=dates, last_updated_time=last_updated_str)

if __name__ == '__main__':
    app.run(debug=True)