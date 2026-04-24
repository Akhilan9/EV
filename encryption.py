from cryptography.fernet import Fernet
import json
import base64

# In a real-world scenario, this key would be securely managed.
# For this project, we'll generate and reuse one.
_KEY = Fernet.generate_key()
cipher_suite = Fernet(_KEY)

def encrypt_data(data_dict):
    """
    Encrypts a dictionary of data into a Fernet token.
    """
    json_data = json.dumps(data_dict).encode('utf-8')
    encrypted_data = cipher_suite.encrypt(json_data)
    return encrypted_data.decode('utf-8')

def decrypt_data(encrypted_token):
    """
    Decrypts a Fernet token back into a dictionary.
    """
    decrypted_data = cipher_suite.decrypt(encrypted_token.encode('utf-8'))
    return json.loads(decrypted_data.decode('utf-8'))

def get_key_base64():
    return base64.b64encode(_KEY).decode('utf-8')
