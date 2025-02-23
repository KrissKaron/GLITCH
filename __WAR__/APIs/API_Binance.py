from binance.client import Client
import time, hmac, hashlib, requests
from binance.exceptions import BinanceAPIException

class API_Binance:
    def __init__(self, public, private):
        self.public_key = public
        self.secret_key = private

    def get_server_time(self):
        url = f"https://api.binance.com/api/v3/time"
        response = requests.get(url)
        if response.status_code == 200:
            server_time = response.json()['serverTime']
            return server_time
        else:
            raise Exception(f"Error fetching server time: {response.text}")

    def signed_request(self, method, params=None):
        if params is None:
            params = {}
        server_time = self.get_server_time()
        params['timestamp'] = server_time
        query_string = '&'.join([f"{key}={value}" for key, value in params.items()])
        signature = hmac.new(self.secret_key.encode(), query_string.encode(), hashlib.sha256).hexdigest()
        params['signature'] = signature

        headers = {
            'X-MBX-APIKEY': self.public_key
        }

        url = f"https://api.binance.com/api/v3/account"

        # Perform request
        if method == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method == "POST":
            response = requests.post(url, headers=headers, params=params)
        else:
            raise Exception("Method not supported")
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error in signed request: {response.text}")

    def execute(self):
        max_retries = 5
        retry_count = 0
        while retry_count < max_retries:
            try:
                client = Client(self.public_key, self.secret_key)
                server_time = self.get_server_time()
                self.signed_request("GET")
                account_snapshot = client.get_account_snapshot(type='SPOT', timestamp=server_time)
                print(f'{server_time}')
                return client, server_time, account_snapshot
            except BinanceAPIException as e: # APIError(code=-1021): Timestamp for this request was 1000ms ahead of the server's time.
                if e == -1021:
                    print(f"Error: Timestamp mismatch ({e}). Retrying in 10 seconds...")
                    retry_count += 1
                    time.sleep(1) # Wait for 10 seconds before retrying
        return client, server_time, account_snapshot