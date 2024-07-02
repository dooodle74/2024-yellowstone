import requests
import json

def fetch_and_save_json(url, filename):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()  # Parse the JSON data
        
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)
        
        print(f"JSON data has been successfully saved to {filename}")
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
    except ValueError as e:
        print(f"Error parsing JSON data: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

# URL of the JSON file
url = "https://webapi.xanterra.net/v1/api/availability/hotels/yellowstonenationalparklodges?date=07%2F11%2F2024&limit=31&is_group=false"

# Filename to save the JSON data
filename = "yellowstone_availability.json"

# Fetch and save the JSON data
fetch_and_save_json(url, filename)