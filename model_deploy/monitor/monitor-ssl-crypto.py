import os
import json
from flask import Flask, jsonify
import ssl
import threading
import socket
import time
from datetime import datetime 
from register import get_system_info, get_file_metadata
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

app = Flask(__name__)

# AES encryption key (must be the same for both scripts)
encryption_key = bytearray.fromhex('121506759454a8bc0ee9e8d509eabda6d04a864caf56f5c0e71a1ae64f02332f')
format = "%d-%m-%Y"
AI = {
    'age_changed': False,
    'context_changed': False,
    'unauthorized_changed': False,
    'Time_of_Change':datetime.now().strftime('%Y-%m-%d %H:%M:%S')
}

def encrypt_response(response):
    backend = default_backend()
    # print(type(response))
    # response = bytearray(response)
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(response) + padder.finalize()

    iv = os.urandom(16)  # Initialization Vector
    cipher = Cipher(algorithms.AES(encryption_key), modes.CBC(iv), backend=backend)
    encryptor = cipher.encryptor()
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

    return iv + encrypted_data
    
def age_tracker(model_metadata, info):
    if (model_metadata['created_time'] != info['created_time']) or (model_metadata['modified_time'] != info['modified_time']):
        return True
    else:
        return False

def context_checker(system_info, info):
    if (system_info['os_version'] != info['os_version']) or (system_info['python_version'] != info['python_version']) or (system_info['flask_version'] != info['flask_version']):
        return True
    else:
        return False

def unauthorized_change_tracker(model_metadata, info):
    if model_metadata['owner'] != info['owner']:
        return True
    else:
        return False

def monitor_changes():
    while True:
        try:
            model_filepath = "/home/monitor/SFAIR_workspace/model_deploy/app/remote/gender_detection.h5"
            initial_context = "/home/monitor/SFAIR_workspace/SFAIR/monitor/remote_model.json"

            # Get real-time system information
            system_info = get_system_info()
            # Get current file metadata
            metadata = get_file_metadata(model_filepath)

            # Load initial context from remote_model.json
            with open(initial_context, 'r') as file:
                info = json.load(file)

            # Check for changes
            age_changed = age_tracker(metadata, info)
            context_changed = context_checker(system_info, info)
            unauthorized_changed = unauthorized_change_tracker(metadata, info)

            # Log detected changes
            changes = {}
            if age_changed:
                changes['age_changed'] = True
                AI['age_changed'] = True
            if context_changed:
                changes['context_changed'] = True
                AI['context_changed'] = True
            if unauthorized_changed:
                changes['unauthorized_changed'] = True
                AI['unauthorized_changed'] = True
            print(changes)  # For demonstration, you can replace this with logging

        except Exception as e:
            print(f"An error occurred: {e}")  # For demonstration, you can replace this with logging

        # Sleep for 20 seconds before checking again
        time.sleep(20)

# Start the monitoring process in a background thread
monitor_thread = threading.Thread(target=monitor_changes)
monitor_thread.daemon = True
monitor_thread.start()

# Setup SSL context
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain(certfile="server.crt", keyfile="server.key")

# Create a socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(("localhost", 5050))
server_socket.listen(1)

def handle_ssl():

    while True:

    # Accept connection from the assessor
        conn, addr = server_socket.accept()
        print("Connected to assessor:", addr)

    # Wrap the connection with SSL
        conn_ssl = ssl_context.wrap_socket(conn, server_side=True)

    # Receive data from the assessor
        data = conn_ssl.recv(1024)
        if data:
            print("Received data from assessor:", data.decode())

        # Send response to the assessor
            response = "Data received successfully"
            conn_ssl.sendall(response)

    # Close the connection
        conn_ssl.close()

ssl_handle_thread = threading.Thread(target=monitor_changes)
ssl_handle_thread.daemon = True
ssl_handle_thread.start()

import json
@app.route('/')
def index():
    print("recv a request")
    # response_json = json.dumps(model)
    response_json = json.dumps(AI).encode('utf-8')
    encrypted_response = encrypt_response(response_json)
    return encrypted_response

if __name__ == "__main__":
    app.run(debug=True)
