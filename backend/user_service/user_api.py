from flask import Flask, jsonify, request
import mysql.connector
import os
import jwt
import datetime
import base64
from decode_auth_token import decode_token, token_required
from cryptography.fernet import Fernet
from get_secrets import get_secret_value
app = Flask(__name__)


SECRET_KEY = get_secret_value(os.environ.get('SECRET_KEY'))
if not SECRET_KEY:
    raise ValueError("No SECRET_KEY set for Flask application")

FERNET_KEY = base64.urlsafe_b64decode(get_secret_value("/run/secrets/cryptography_key")) 
if not FERNET_KEY:
    raise ValueError("No FERNET_KEY set for Flask application")
cipher_suite = Fernet(FERNET_KEY)


def get_db_connection():
    ssl_ca = "/run/secrets/db_https_user_cert"
    ssl_cert = "/run/secrets/db_https_user_cert"
    ssl_key = "/run/secrets/db_https_user_key"

    if not os.path.exists(ssl_ca) or not os.path.exists(ssl_cert) or not os.path.exists(ssl_key):
        raise ValueError("One or more SSL certificate files are missing!")

    return mysql.connector.connect(
        host=os.environ.get("DB_HOST"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        database=os.environ.get("DB_NAME"),
        ssl_ca=ssl_ca,
        ssl_cert=ssl_cert,
        ssl_key=ssl_key,
        
    )

def create_initial_users():
    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute("SELECT * FROM UserData WHERE username = 'admin';")
    if not cursor.fetchone():
        encrypted_psw_admin = cipher_suite.encrypt('gachana'.encode())
        cursor.execute("INSERT INTO UserData (username, psw, role) VALUES (%s, %s, %s);", ('admin', encrypted_psw_admin, 'Admin'))
        print("Admin user created.")
    
    cursor.execute("SELECT * FROM UserData WHERE username = 'player';")
    if not cursor.fetchone():
        encrypted_psw_player = cipher_suite.encrypt('prova'.encode())
        cursor.execute("INSERT INTO UserData (username, psw, role) VALUES (%s, %s, %s);", ('player', encrypted_psw_player, 'Player'))
        print("Player user created.")
    
    connection.commit()
    cursor.close()
    connection.close()

create_initial_users()

# Gestione del token
def generate_auth_token(user_id, role):
    expiration_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    return jwt.encode({'user_id': user_id, 'role': role, 'exp': expiration_time},
                       SECRET_KEY, algorithm="HS256")

@app.route('/signup', methods=['POST'])
def registration():
    data = request.get_json()

    if not data.get('username') or not data.get('psw'):
        return jsonify({'message': 'Incomplete data'}), 400

    username = data['username']
    psw = data['psw']
    role = 'Player'
   
    
    encrypted_psw = cipher_suite.encrypt(psw.encode())

    connection = get_db_connection()
    cursor = connection.cursor()
   
    cursor.execute("SELECT * FROM UserData WHERE username = %s;", (username,))
    existing_user = cursor.fetchone()

    if existing_user:
        cursor.close()
        connection.close()
        return jsonify({'message': 'Username already exists'}), 400

    cursor.execute(
        "INSERT INTO UserData (username, psw, role) VALUES (%s, %s, %s);",
        (username, encrypted_psw, role)
    )

    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({'message': 'User added!'}), 201

# Autenticazione per ottenere il token
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data.get('username') or not data.get('psw'):
        return jsonify({'message': 'Incomplete data'}), 400
    
    username, password = data.get('username'), data.get('psw')

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT id, role, psw FROM UserData WHERE username=%s", (username,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()
    print(f"psw: ", user['psw'])
    if user:
        decrypted_psw = cipher_suite.decrypt(user['psw']).decode()

        if decrypted_psw == password:
            token = generate_auth_token(user['id'], user['role'])
            return jsonify({'token': token})

    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/logout', methods=['POST'])
@token_required(role_required=['Admin', 'Player'])
def logout():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    token_status = decode_token(token)
    
    if token_status == 'Token expired':
        return jsonify({"message": "Token has expired!"}), 403
    elif token_status == 'Invalid token':
        return jsonify({"message": "Invalid token!"}), 403

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT token FROM TokenBlacklist WHERE token = %s;", (token,))
        existing_token = cursor.fetchone()
        
        if existing_token:
            return jsonify({"message": "Token is already logged out!"}), 400  

        cursor.execute("INSERT INTO TokenBlacklist (token) VALUES (%s);", (token,))

        cursor.execute("SELECT token FROM TokenBlacklist;")
        tokens = cursor.fetchall() 

        for row in tokens:
            blacklisted_token = row[0]
            token_status = decode_token(blacklisted_token)
            if token_status == 'Token expired':
                cursor.execute("DELETE FROM TokenBlacklist WHERE token = %s;", (blacklisted_token,))

        connection.commit()
        cursor.close()
        connection.close()
    except Exception as e:
        return jsonify({"message": "An error occurred while logging out.", "error": str(e)}), 500

    return jsonify({"message": "Logged out successfully!"}), 200




# ADMIN ENDPOINT

@app.route('/list', methods=['GET'])
@token_required(role_required='Admin')
def get_users():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM UserData;")
    users_list = cursor.fetchall()
    cursor.close()
    connection.close()

    return jsonify({'users': users_list})

@app.route('/<int:user_id>', methods=['GET'])
@token_required(role_required='Admin')
def get_user(user_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM UserData WHERE id = %s;", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()

    return jsonify({'user': user})

@app.route('/<int:user_id>/update', methods=['PATCH'])
@token_required(role_required='Admin')
def update_user(user_id):
    data = request.get_json()

    if not data.get('username') and not data.get('psw') and not data.get('role') and not data.get('id_image'):
        return jsonify({'message': 'No data provided for update'}), 400

    username = data.get('username')
    psw = data.get('psw')
    role = data.get('role')
    id_image = data.get('id_image')

    connection = get_db_connection()
    cursor = connection.cursor()

    query = "UPDATE UserData SET "
    params = []

    if username:
        query += "username = %s, "
        params.append(username)
    if psw:
        query += "psw = %s, "
        params.append(psw)
    if role:
        query += "role = %s, "
        params.append(role)
    if id_image:
        query += "id_image = %s, "
        params.append(id_image)

    query = query.rstrip(', ')

    query += " WHERE id = %s"
    params.append(user_id)

    cursor.execute(query, tuple(params))
    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({'message': 'User updated successfully'}), 200

@app.route('/<int:user_id>/delete', methods=['DELETE'])
@token_required(role_required='Admin')
def delete_account_admin(user_id):

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM UserData WHERE id = %s;", (user_id,))
    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({'message': 'User account deleted successfully!'}), 200


# USER ENDPOINT

@app.route('/delete', methods=['DELETE'])
@token_required(role_required='Player')
def delete_account():
    
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_data = decode_token(token)
    if not user_data:
        return jsonify({'message':'Could not access user data.'}), 401
    user_id = user_data.get('user_id')
    if not user_id:
        return jsonify({'message':'Could not access user id.'}), 401

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM UserData WHERE id = %s;", (user_id,))
    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({'message': 'User account deleted successfully!'}), 200

@app.route('/update', methods=['PATCH'])
def update_account():
    
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_data = decode_token(token)
    if not user_data:
        return jsonify({'message':'Could not access user data.'}), 401
    user_id = user_data.get('user_id')
    if not user_id:
        return jsonify({'message':'Could not access user id.'}), 401

    data = request.get_json()

    if not data.get('username') and not data.get('psw') and not data.get('id_image'):
        return jsonify({'message': 'No data provided for update'}), 400

    username = data.get('username')
    psw = data.get('psw')
    id_image = data.get('id_image')

    connection = get_db_connection()
    cursor = connection.cursor()

    query = "UPDATE UserData SET "
    params = []

    if username:
        query += "username = %s, "
        params.append(username)
    if psw:
        query += "psw = %s, "
        params.append(psw)
    if id_image:
        query += "id_image = %s, "
        params.append(id_image)

    query = query.rstrip(', ')

    query += " WHERE id = %s"
    params.append(user_id)

    cursor.execute(query, tuple(params))
    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({'message': 'User information updated successfully'}), 200


   
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, ssl_context=('/run/secrets/https_user_cert', '/run/secrets/https_user_key'))

