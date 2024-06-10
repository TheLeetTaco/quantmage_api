from qm_dataclass import Quantmage_Data
import requests
import json
import time
import os

class Quantmage_API:
    def __init__(self, endpoint_id):
        self.endpoint_id = endpoint_id
        self.url = f'https://quantmage.app/grimoire/backtest/{self.endpoint_id}'
        self.data_file = f'{self.endpoint_id}.json'
        self.response_data = None
        self.fetch_data()
        self.data = self.load_data()

    def fetch_data(self):
        params = {
            "extra" : True
        }
        
        # Make the POST request
        response = requests.post(self.url, params=params)
        
        # Save to a file
        with open(self.data_file, 'w') as json_file:
            json.dump(response.json(), json_file)
            
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            
            self.response_data = response.json()
            
            print("Data has been collected")
        else:
            print(f"Request failed with status code {response.status_code}")
        
        # Date check
        pull_dates = False
        if os.path.exists('dates.json'):
            with open('dates.json', 'r') as file:
                raw_dates = json.load(file)["dates"]
            dates = raw_dates[raw_dates.index(max(self.response_data.get("data_ranges"))):]
            backtest_len = self.response_data["value_history"]
        else:
            pull_dates = True
            
        # If our value history is longer then our dates
        if pull_dates or (len(backtest_len) > len(dates)):
            # Then we need to pull do a non extra api pull
            print("Missing Dates Pulling")
            response = requests.post(self.url)
            with open('dates.json', 'w') as json_file:
                print(response["dates"][-1])
                json.dump({"dates": response["dates"]}, json_file)

    def load_data(self):
        return Quantmage_Data.from_json(self.response_data)

def batch_collect(ids):
    collection = []
    # We can only do one per second
    for id in ids:
        collection.append(Quantmage_API(id))
        time.sleep(1)
    
    return collection

if __name__ == "__main__":
    # Example usage
    endpoint_id = '81e1430056f8e243f6ff97855738bdca'
    quantmage_output = Quantmage_API(endpoint_id)
