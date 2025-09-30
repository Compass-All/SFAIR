import requests
from requests.exceptions import ConnectionError
import ssl
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from urlconfig import *

url = monitor_url
retry_attempts = 3
timeout_seconds = 10
encryption_key = bytearray.fromhex('121506759454a8bc0ee9e8d509eabda6d04a864caf56f5c0e71a1ae64f02332f')
certificate_path = 'server.crt'

def decrypt_response(iv, encrypted_data):
    backend = default_backend()
    cipher = Cipher(algorithms.AES(encryption_key), modes.CBC(iv), backend=backend)
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(encrypted_data) + decryptor.finalize()

    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    decrypted_data = unpadder.update(padded_data) + unpadder.finalize()

    return decrypted_data

def make_request(url):
    try:
        response = requests.get(url, timeout=timeout_seconds, verify=certificate_path)
        # Handle response
        iv = response.content[:16]  # Extract IV
        encrypted_data = response.content[16:]
        #print('this is ok',encrypted_data)
        decrypted_response = decrypt_response(iv, encrypted_data)
        return decrypted_response.decode()
    except ConnectionError as e:
        print("Connection error:", e)
        return None

def main():
    for attempt in range(1, retry_attempts + 1):
        print(f"Attempt {attempt}...")
        response = make_request(url)
        if response is not None:
            print("Request successful")
            # Process response
            break
        elif attempt < retry_attempts:
            print("Retrying...")
        else:
            print("Max retries exceeded")


if __name__ == "__main__":
    main()
