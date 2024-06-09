from collections import defaultdict
import matplotlib.pyplot as plt
from qm_dataclass import Data
import requests
import json

# Define the endpoint identifier
endpoint_id = 'fc1a05b33b8e2a170584844265dfd998'

# Construct the API endpoint URL
url = f'https://quantmage.app/grimoire/backtest/{endpoint_id}'

# Make the POST request
response = requests.post(url)

# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON response
    data = response.json()
    
    # Save the data to a JSON file
    with open('data.json', 'w') as json_file:
        json.dump(data, json_file)
    
    print("Data has been saved to data.json")
else:
    print(f"Request failed with status code {response.status_code}")

data_obj = Data('data.json')

