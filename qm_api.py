from qm_dataclass import Spell
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
            "extra" :"true"
        }
        
        # Make the POST request
        response = requests.post(self.url, params=params)
            
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            self.response_data = response.json()
            # Save to a file
            with open(self.data_file, 'w') as json_file:
                json.dump(self.response_data, json_file)
            print("Data has been collected")
        else:
            print(f"Request failed with status code {response.status_code}")
        
        # Date check
        pull_dates = True
        if os.path.exists('dates.json'):
            with open('dates.json', 'r') as file:
                raw_dates = json.load(file)["dates"]
            dates = raw_dates[raw_dates.index(max(self.response_data.get("data_ranges"))):]
            backtest_len = self.response_data["value_history"]
        else:
            pull_dates = True
            
        # If our value history is longer then our dates
        if pull_dates or (len(backtest_len) > len(dates)):
            # Then we need to pull doing a non extra api pull
            print("Missing Dates Pulling")
            response = requests.post(self.url).json()
            with open('dates.json', 'w') as json_file:
                print(response["dates"][-1])
                json.dump({"dates": response["dates"]}, json_file)
            print("Dates Updated")

    def load_data(self):
        return Spell.from_json(self.response_data)

def batch_collect(ids):
    collection = []
    # We can only do one per second
    for id in ids:
        collection.append(Quantmage_API(id))
        time.sleep(1)
    
    return collection

if __name__ == "__main__":
    # Example usage
    endpoint_id = 'ba7158f9bf6d88ea87db0341f6c4a849'
    quantmage_output = Quantmage_API(endpoint_id)
