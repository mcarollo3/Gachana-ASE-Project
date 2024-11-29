from cryptography.fernet import Fernet
import base64

# Genera una chiave Fernet
key = "MldtYnpabEgyZWl4OVJHX3JSMXZWX3dxVzU2NEl0VjRFTW0tQ05TV2lCWT0="


fernet_key = base64.urlsafe_b64decode(key)
print(f"ferne")

cipher_suite = Fernet(fernet_key)

psw = 'gachana'

encrypted_psw = cipher_suite.encrypt(psw.encode())

print(encrypted_psw)