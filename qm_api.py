from qm_dataclass import Quantmage_Data
import requests
import json

class Quantmage_API:
    def __init__(self, endpoint_id):
        self.endpoint_id = endpoint_id
        self.url = f'https://quantmage.app/grimoire/backtest/{self.endpoint_id}'
        self.data_file = f'{self.endpoint_id}.json'
        self.response_data = None
        self.fetch_data()
        self.data = self.load_data()

    def fetch_data(self):
        # Make the POST request
        response = requests.post(self.url)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            self.response_data = response.json()
            
            print("Data has been collected")
        else:
            print(f"Request failed with status code {response.status_code}")

    def save_data(self):
        with open(self.data_file, 'w') as json_file:
            json.dump(self.response_data, json_file)

    def load_data(self):
        return Quantmage_Data.from_json(self.response_data)

if __name__ == "__main__":
    # Example usage
    endpoint_id = '81e1430056f8e243f6ff97855738bdca'
    quantmage_output = Quantmage_API(endpoint_id)
    print("Test")
