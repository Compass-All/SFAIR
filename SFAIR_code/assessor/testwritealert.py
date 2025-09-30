import json
from datetime import datetime
from secureconnect import make_request  # Importing make_request from secureconnect module


data_storage = {}
def test(host):

    return make_request(host)

def write_monitor_alert_to_json(host):
    # Call make_request function from secureconnect module
    data_storage['data'] = test(host)
    with open("test_write.json", "w") as json_file:
            json.dump(data_storage, json_file, indent=4)
    
    #print(data_storage['data'])
    #print(testa)
    
    
def main():
    # Define the URL
    url = 'http://127.0.0.1:5010/'
    # Call the function to write response to JSON file
    #test(url)
    write_monitor_alert_to_json(url)	
    
if __name__ == "__main__":
    main()
