from flask import Flask, jsonify, request
import time
import mysql.connector
from mysql.connector import Error
import os
import jwt
import datetime
import base64
from decode_auth_token import decode_token, token_required
from cryptography.fernet import Fernet
from get_secrets import get_secret_value
import re

app = Flask(__name__)

TOKEN_EXPIRED = "Token expired"
INVALID_TOKEN = "Invalid token"


SECRET_KEY = get_secret_value(os.environ.get("SECRET_KEY"))
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

    max_retries = 5
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            connection = mysql.connector.connect(
                host=os.environ.get("DB_HOST"),
                user=get_secret_value(os.environ.get("DB_USER")),
                password=get_secret_value(os.environ.get("DB_PASSWORD")),
                database=os.environ.get("DB_NAME"),
                ssl_ca=ssl_ca,
                ssl_cert=ssl_cert,
                ssl_key=ssl_key,
            )

            if connection.is_connected():
                print("Database connection successful!")
                return connection
        except Error as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt + 1 < max_retries:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Max retries reached. Exiting.")
                raise e

    raise Exception("Unable to connect to the database after multiple attempts.")


def create_initial_users():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM UserData WHERE username = 'admin';")
    if not cursor.fetchone():
        encrypted_psw_admin = cipher_suite.encrypt("gachana".encode())
        cursor.execute(
            "INSERT INTO UserData (username, psw, role) VALUES (%s, %s, %s);",
            ("admin", encrypted_psw_admin, "Admin"),
        )
        print("Admin user created.")

    cursor.execute("SELECT * FROM UserData WHERE username = 'player';")
    if not cursor.fetchone():
        encrypted_psw_player = cipher_suite.encrypt("prova".encode())
        cursor.execute(
            "INSERT INTO UserData (username, psw, role) VALUES (%s, %s, %s);",
            ("player", encrypted_psw_player, "Player"),
        )
        print("Player user created.")

    cursor.execute("SELECT * FROM UserData WHERE username = 'player2';")
    if not cursor.fetchone():
        encrypted_psw_player2 = cipher_suite.encrypt("prova".encode())
        cursor.execute(
            "INSERT INTO UserData (username, psw, role) VALUES (%s, %s, %s);",
            ("player2", encrypted_psw_player2, "Player"),
        )
        print("Player2 user created.")

    connection.commit()
    cursor.close()
    connection.close()


create_initial_users()


# Gestione del token
def generate_auth_token(user_id, role):
    expiration_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        hours=1
    )
    return jwt.encode(
        {"user_id": user_id, "role": role, "exp": expiration_time},
        SECRET_KEY,
        algorithm="HS256",
    )


def sanitize_username(input_str):
    """Permette solo caratteri alfanumerici, underscore e trattini."""
    return re.sub(r"[^a-zA-Z0-9_-]", "", input_str)


def is_valid_password(password):
    """Verifica se la password soddisfa i criteri di sicurezza."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number."
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character."
    return True, ""


# Endpoint di registrazione con validazione
@app.route("/signup", methods=["POST"])
def registration():
    data = request.get_json()

    if not data.get("username") or not data.get("psw"):
        return jsonify({"message": "Incomplete data"}), 400

    username = sanitize_username(data["username"])
    psw = data["psw"]

    is_valid, error_message = is_valid_password(psw)
    if not is_valid:
        return jsonify({"message": error_message}), 400

    encrypted_psw = cipher_suite.encrypt(psw.encode())

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM UserData WHERE username = %s;", (username,))
    existing_user = cursor.fetchone()

    if existing_user:
        cursor.close()
        connection.close()
        return jsonify({"message": "Username already exists"}), 400

    cursor.execute(
        "INSERT INTO UserData (username, psw, role) VALUES (%s, %s, %s);",
        (username, encrypted_psw, "Player"),
    )

    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({"message": f"User {username} added!"}), 201


@app.route("/check_token_blacklist", methods=["POST"])
def check_token_blacklist():
    # Ottieni il token dalla richiesta
    data = request.get_json()
    token = data.get("token")

    # Verifica se il token è presente nella blacklist
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT token FROM TokenBlacklist WHERE token = %s;", (token,))
    blacklisted_token = cursor.fetchone()

    cursor.close()
    connection.close()

    if blacklisted_token:
        return jsonify({"message": "Token is blacklisted!"}), 403
    else:
        return jsonify({"message": "Token is not blacklisted."}), 200


# Endpoint di login con sanificazione input
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data.get("username") or not data.get("psw"):
        return jsonify({"message": "Incomplete data"}), 400

    username = sanitize_username(data["username"])
    password = data["psw"]

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT id, role, psw FROM UserData WHERE username=%s", (username,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()

    if user:
        decrypted_psw = cipher_suite.decrypt(user["psw"]).decode()

        if decrypted_psw == password:
            token = generate_auth_token(user["id"], user["role"])
            return jsonify({"token": token})

    return jsonify({"message": "Invalid credentials"}), 401


@app.route("/logout", methods=["POST"])
@token_required(role_required=["Admin", "Player"])
def logout():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")

    token_status = decode_token(token)

    if token_status == TOKEN_EXPIRED:
        return jsonify({"message": "Token has expired!"}), 403
    elif token_status == INVALID_TOKEN:
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
            if token_status == "Token expired":
                cursor.execute(
                    "DELETE FROM TokenBlacklist WHERE token = %s;", (blacklisted_token,)
                )

        connection.commit()
        cursor.close()
        connection.close()
    except Exception as e:
        return (
            jsonify(
                {"message": "An error occurred while logging out.", "error": str(e)}
            ),
            500,
        )

    return jsonify({"message": "Logged out successfully!"}), 200


# ADMIN ENDPOINT


@app.route("/list", methods=["GET"])
@token_required(role_required="Admin")
def get_users():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM UserData;")
    users_list = cursor.fetchall()
    cursor.close()
    connection.close()

    return jsonify({"users": users_list})


@app.route("/<int:user_id>", methods=["GET"])
@token_required(role_required="Admin")
def get_user(user_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM UserData WHERE id = %s;", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()

    return jsonify({"user": user})


@app.route("/<int:user_id>/update", methods=["PATCH"])
@token_required(role_required="Admin")
def update_user(user_id):
    data = request.get_json()

    if not data.get("username") and not data.get("psw") and not data.get("role"):
        return jsonify({"message": "No data provided for update"}), 400

    username = sanitize_username(data.get("username")) if data.get("username") else None
    psw = data.get("psw")
    role = data.get("role")

    # Validate password if provided
    if psw:
        is_valid, error_message = is_valid_password(psw)
        if not is_valid:
            return jsonify({"message": error_message}), 400

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

    query = query.rstrip(", ")

    query += " WHERE id = %s"
    params.append(user_id)

    cursor.execute(query, tuple(params))
    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({"message": "User updated successfully"}), 200


@app.route("/<int:user_id>/delete", methods=["DELETE"])
@token_required(role_required="Admin")
def delete_account_admin(user_id):

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM UserData WHERE id = %s;", (user_id,))
    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({"message": "User account deleted successfully!"}), 200


# USER ENDPOINT


@app.route("/delete", methods=["DELETE"])
@token_required(role_required="Player")
def delete_account():

    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_data = decode_token(token)
    if not user_data:
        return jsonify({"message": "Could not access user data."}), 401
    user_id = user_data.get("user_id")
    if not user_id:
        return jsonify({"message": "Could not access user id."}), 401

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM UserData WHERE id = %s;", (user_id,))
    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({"message": "User account deleted successfully!"}), 200


@app.route("/update", methods=["PATCH"])
def update_account():

    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_data = decode_token(token)
    if not user_data:
        return jsonify({"message": "Could not access user data."}), 401
    user_id = user_data.get("user_id")
    if not user_id:
        return jsonify({"message": "Could not access user id."}), 401

    data = request.get_json()

    if not data.get("username") and not data.get("psw"):
        return jsonify({"message": "No data provided for update"}), 400

    username = sanitize_username(data.get("username")) if data.get("username") else None
    psw = data.get("psw")

    # Validate password if provided
    if psw:
        is_valid, error_message = is_valid_password(psw)
        if not is_valid:
            return jsonify({"message": error_message}), 400

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

    query = query.rstrip(", ")

    query += " WHERE id = %s"
    params.append(user_id)

    cursor.execute(query, tuple(params))
    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({"message": "User information updated successfully"}), 200


if __name__ == "__main__":
    app.run(
        debug=False,
        host="0.0.0.0",
        port=5000,
        ssl_context=("/run/secrets/https_user_cert", "/run/secrets/https_user_key"),
    )
