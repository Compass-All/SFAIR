import os
import sys
import platform
import subprocess
import json
from datetime import datetime


def get_file_metadata(filepath):
    metadata = {}
    try:
        # File creation time
        created_time = os.path.getctime(filepath)
        d_created_time = datetime.fromtimestamp(created_time)
        metadata['created_time'] = d_created_time.strftime("%Y-%m-%d %H:%M:%S")
        #metadata['created_time'] = datetime.fromtimestamp(created_time)

        # File modified time
        modified_time = os.path.getmtime(filepath)
        d_modified_time = datetime.fromtimestamp(modified_time)
        metadata['modified_time'] = d_modified_time.strftime("%Y-%m-%d %H:%M:%S")
        #metadata['modified_time'] = datetime.fromtimestamp(modified_time)

        # File owner
        owner = os.stat(filepath).st_uid
        metadata['owner'] = owner

        return metadata
    except FileNotFoundError:
        print("File not found.")
    except Exception as e:
        print("An error occurred: {}".format(e))


def get_system_info():
    system_info = {}
    system_info['os_version'] = platform.platform()
    system_info['python_version'] = platform.python_version()
    try:
        flask_version = subprocess.check_output(['pip', 'show', 'Flask']).decode().split('\n')[1].split(': ')[1]
        system_info['flask_version'] = flask_version
    except Exception as e:
        print("Error retrieving Flask version: {}".format(e))
        system_info['flask_version'] = "Unknown"
    return system_info


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python register.py <file_path>")
        sys.exit(1)

    # /home/zombie/SFAIR-workspace/model_deploy/app/gender_classification_model.pth
    filepath = sys.argv[1]
    metadata = get_file_metadata(filepath)
    system_info = get_system_info()

    if metadata and system_info:
        data = {
            'created_time': metadata['created_time'],
            'modified_time': metadata['modified_time'],
            'owner': metadata['owner'],
            'os_version': system_info['os_version'],
            'python_version': system_info['python_version'],
            'flask_version': system_info['flask_version']
        }

        with open("remote_model.json", "w") as json_file:
            json.dump(data, json_file, indent=4)

        print("Model information saved in remotemodel.json.")
