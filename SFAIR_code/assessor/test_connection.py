import requests
from requests.exceptions import ConnectionError

url = 'http://127.0.0.1:5010/'
retry_attempts = 3
timeout_seconds = 5

def make_request(url):
    try:
        response = requests.get(url, timeout=timeout_seconds)
        # Handle response
        return response
    except ConnectionError as e:
        print("Connection error:", e)
        return None

def main():
    for attempt in range(1, retry_attempts + 1):
        print(f"Attempt {attempt}...")
        response = make_request(url)
        if response is not None and response.status_code == 200:
            print("Request successful")
            # Process response
            break
        elif attempt < retry_attempts:
            print("Retrying...")
        else:
            print("Max retries exceeded")

if __name__ == "__main__":
    main()
