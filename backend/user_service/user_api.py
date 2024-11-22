from flask import Flask, jsonify, request
import mysql.connector
import os
import jwt
import datetime
from decode_auth_token import decode_token, token_required

app = Flask(__name__)
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("No SECRET_KEY set for Flask application")

# Get Connection DB
def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        database=os.environ.get("DB_NAME")
    )

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
        (username, psw, role)
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
    
    username, password = data.get('username'), data.get('password')

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT id, role FROM UserData WHERE username=%s AND psw=%s", (username, password))
    user = cursor.fetchone()
    cursor.close()
    connection.close()

    if user:
        token = generate_auth_token(user['id'], user['role'])
        return jsonify({'token': token})
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/logout', methods=['POST'])
def logout():
    return jsonify({"message": "You have successfully logged out!"}), 200


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

    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_data = decode_token(token)
    user_id = user_data['user_id']

    data = request.get_json()
    amount = data.get('amount')
    card_number = data.get('card_number')
    expiry_date = data.get('expiry_date')
    cvv = data.get('cvv')

    if not amount or amount <= 0:
        return jsonify({'message': 'Invalid amount. Must be greater than zero.'}), 400

    if not card_number or not expiry_date or not cvv:
        return jsonify({'message': 'Invalid card details. All fields are required.'}), 400

    payment_successful = simulate_payment(card_number, expiry_date, cvv, amount)
    if not payment_successful:
        return jsonify({'message': 'Payment failed. Please check your card details.'}), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("UPDATE UserData SET wallet = wallet + %s WHERE id = %s;", (amount, user_id))
    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({'message': f'{amount} added to your wallet successfully!'}), 200

   
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
