import os
import json
from register import get_system_info, get_file_metadata
import time

def age_tracker(model_metadata, initial_context):
    # Load information from remote_model.json
    with open(initial_context, 'r') as file:
        info = json.load(file)

    # Compare model creation time with the stored time from remote_model.json
    if model_metadata['created_time'] != info['created_time'] or model_metadata['modified_time'] != info['modified_time']:
        return True
    else:
        return False

def context_checker(system_info, initial_context):
    # Load information from remote_model.json
    with open(initial_context, 'r') as stored_context:
        info = json.load(stored_context)

    # Compare system context information with the stored information from remote_model.json
    print(info)
    
    if  system_info['os_version'] != info['os_version'] or system_info['python_version'] != info['python_version'] or system_info['flask_version'] != info['flask_version']: 
        return True
    else:
        return False

def unauthorized_change_tracker(model_metadata, initial_context):
    # Load information from remote_model.json
    with open(initial_context, 'r') as file:
        info = json.load(file)

    # Compare owner information with the stored owner from remote_model.json
    if model_metadata['owner'] != info['owner']:
        print('An unauthorized change detected in the model file.')
        return True
    else:
        return False

if __name__ == "__main__":

    model_filepath = "/home/h/SFAIR_workspace/model_deploy/app/remote/gender_detection.h5"
    initial_context = "/home/h/SFAIR_workspace/SFAIR/monitor/remote_model.json"
    
    while True:
        # Get real-time system information
        system_info = get_system_info()
        # Get current file metadata
        metadata = get_file_metadata(model_filepath)

        # Check for changes
        age_changed = age_tracker(metadata, initial_context)
        context_changed = context_checker(system_info, initial_context)
        unauthorized_changed = unauthorized_change_tracker(metadata, initial_context)

        # Log detected changes
        if age_changed:
            print("Age of the model has changed.")
        if context_changed:
            print("System context has changed.")
        if unauthorized_changed:
            print("Unauthorized change detected in the model file.")

        # Sleep for 20 seconds
        time.sleep(20)
