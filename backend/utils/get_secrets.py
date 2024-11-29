

def get_secret_value(secret_path):
    with open(secret_path, 'r') as secret_file:
        return secret_file.read().strip()