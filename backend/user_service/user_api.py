from flask import Flask, jsonify, request
import mysql.connector
import os
import jwt
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key')

# Get Connection DB
def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        database=os.environ.get("DB_NAME")
    )


# Gestione del token
def generate_token(user_id, role):
    expiration_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    return jwt.encode({'user_id': user_id, 'role': role, 'exp': expiration_time},
                       app.config['SECRET_KEY'], algorithm="HS256")

def decode_token(token):
    try:
        return jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def token_required(role_required):
    def decorator(f):
        def wrapped_function(*args, **kwargs):
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            if not token:
                return jsonify({'message': 'Token is missing!'}), 403
            
            user_data = decode_token(token)
            if user_data is None or user_data['role'] != role_required:
                return jsonify({'message': 'Unauthorized access!'}), 403

            return f(*args, **kwargs)
        wrapped_function.__name__ = f.__name__  
        return wrapped_function
    return decorator

# Autenticazione per ottenere il token
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username, password = data.get('username'), data.get('password')

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT id, role FROM UserData WHERE username=%s AND psw=%s", (username, password))
    user = cursor.fetchone()
    cursor.close()
    connection.close()

    if user:
        token = generate_token(user['id'], user['role'])
        return jsonify({'token': token})
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/logout', methods=['POST'])
def logout():
    return jsonify({"message": "You have successfully logged out!"}), 200

@app.route('/admin_only', methods=['GET'])
@token_required(role_required='Admin')
def admin_only():
    return jsonify({"message": "Welcome, Admin!"})

@app.route('/player_area', methods=['GET'])
@token_required(role_required='Player')
def player_area():
    return jsonify({"message": "Welcome, Player!"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
