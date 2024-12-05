from flask import Flask, json, request, make_response, jsonify
import time
import mysql.connector
from mysql.connector import Error
import os
from decode_auth_token import decode_token, token_required
from decimal import Decimal
from get_secrets import get_secret_value
import re
from werkzeug.exceptions import BadRequest


# Sanificazione generale dei dati
def sanitize_input(value):
    if isinstance(value, str):
        value = re.sub(r"[<>;'\"\\]", "", value).strip()
    elif isinstance(value, list):
        value = [sanitize_input(v) for v in value]
    elif isinstance(value, dict):
        value = {k: sanitize_input(v) for k, v in value.items()}
    return value


# Sanificazione di numeri o valori decimali
def sanitize_decimal(value):
    try:
        return Decimal(value)
    except:
        raise BadRequest("Invalid decimal format.")


app = Flask(__name__)
SECRET_KEY = get_secret_value(os.environ.get("SECRET_KEY"))
if not SECRET_KEY:
    raise ValueError("No SECRET_KEY set for Flask application")


# Get Connection DB
def get_db_connection():
    ssl_ca = "/run/secrets/db_https_currency_cert"
    ssl_cert = "/run/secrets/db_https_currency_cert"
    ssl_key = "/run/secrets/db_https_currency_key"

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


def simulate_payment(card_number, expiry_date, cvv):
    if len(card_number) == 16 and len(expiry_date) == 5 and len(cvv) == 3:
        return True
    return False


@app.route("/check_and_deduct", methods=["POST"])
@token_required(role_required="Player")
def check_and_deduct_wallet():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_data = decode_token(token)
    if not user_data:
        return jsonify({"message": "Could not access user data."}), 401

    user_id = user_data.get("user_id")
    if not user_id:
        return jsonify({"message": "Could not access user id."}), 401

    # Sanifichiamo i dati di input
    data = sanitize_input(request.get_json())
    amount_to_deduct = sanitize_decimal(data.get("amount", 0))

    if not amount_to_deduct or amount_to_deduct <= 0:
        return jsonify({"message": "Invalid amount. Must be greater than zero."}), 403

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT id, wallet FROM Wallets WHERE user_id = %s;", (user_id,))
    wallet_data = cursor.fetchone()

    if not wallet_data:
        return jsonify({"message": "Insufficient funds in wallet."}), 403

    wallet_id, current_balance = wallet_data

    if current_balance < amount_to_deduct:
        return (
            jsonify(
                {
                    "message": "Insufficient funds in wallet.",
                    "available_funds": str(current_balance),
                }
            ),
            403,
        )

    new_balance = current_balance - amount_to_deduct
    cursor.execute(
        "UPDATE Wallets SET wallet = %s WHERE id = %s;", (new_balance, wallet_id)
    )

    description = f"Deducted {amount_to_deduct} from wallet."
    cursor.execute(
        """
        INSERT INTO Transaction_History (wallet_id, user_id, old_wallet, new_wallet, description, date)
        VALUES (%s, %s, %s, %s, %s, NOW());
        """,
        (wallet_id, user_id, current_balance, new_balance, description),
    )

    connection.commit()

    cursor.close()
    connection.close()

    return (
        jsonify(
            {"message": "Funds deducted successfully!", "new_balance": str(new_balance)}
        ),
        200,
    )


@app.route("/buy_currency", methods=["PATCH"])
@token_required(role_required="Player")
def add_funds():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_data = decode_token(token)
    if not user_data:
        return jsonify({"message": "Could not access user data."}), 401
    user_id = user_data.get("user_id")
    if not user_id:
        return jsonify({"message": "Could not access user id."}), 401

    # Sanifichiamo i dati di input
    data = sanitize_input(request.get_json())
    amount = sanitize_decimal(data.get("amount"))
    card_number = sanitize_input(data.get("card_number"))
    expiry_date = sanitize_input(data.get("expiry_date"))
    cvv = sanitize_input(data.get("cvv"))

    if not amount or amount <= 0:
        return jsonify({"message": "Invalid amount. Must be greater than zero."}), 400

    if not all([card_number, expiry_date, cvv]):
        return (
            jsonify({"message": "Invalid card details. All fields are required."}),
            400,
        )

    payment_successful = simulate_payment(card_number, expiry_date, cvv)
    if not payment_successful:
        return (
            jsonify({"message": "Payment failed. Please check your card details."}),
            400,
        )

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT id, wallet FROM Wallets WHERE user_id = %s;", (user_id,))
        wallet_data = cursor.fetchone()

        if not wallet_data:
            cursor.execute(
                "INSERT INTO Wallets (user_id, wallet) VALUES (%s, %s);",
                (user_id, 0.00),
            )
            connection.commit()
            cursor.execute(
                "SELECT id, wallet FROM Wallets WHERE user_id = %s;", (user_id,)
            )
            wallet_data = cursor.fetchone()

        wallet_id, old_wallet = wallet_data
        new_wallet = old_wallet + amount * 100  # ogni euro sono 100 lorcano

        cursor.execute(
            "UPDATE Wallets SET wallet = %s WHERE id = %s;", (new_wallet, wallet_id)
        )

        description = f"Added {amount} to wallet via card payment."
        cursor.execute(
            """
            INSERT INTO Transaction_History (wallet_id, user_id, old_wallet, new_wallet, description, date)
            VALUES (%s, %s, %s, %s, %s, NOW());
            """,
            (wallet_id, user_id, old_wallet, new_wallet, description),
        )

        connection.commit()

    except Exception as e:
        connection.rollback()
        return (
            jsonify(
                {
                    "message": "An error occurred while processing the transaction.",
                    "error": str(e),
                }
            ),
            500,
        )

    finally:
        cursor.close()
        connection.close()

    return jsonify({"message": f"{amount*100} added to your wallet successfully!"}), 200


@app.route("/transactions", methods=["GET"])
@token_required(role_required="Player")
def get_transactions():

    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_data = decode_token(token)
    if not user_data:
        return jsonify({"message": "Could not access user data."}), 401

    user_id = user_data.get("user_id")
    if not user_id:
        return jsonify({"message": "Could not access user id."}), 401

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
    SELECT * 
    FROM Transaction_History
    WHERE user_id = %s;
    """
    cursor.execute(query, (user_id,))
    transactions = cursor.fetchall()

    cursor.close()
    connection.close()

    if not transactions:
        return jsonify({"message": "No transactions found for the user."}), 404

    return jsonify(transactions), 200


@app.route("/transactions/list", methods=["GET"])
@token_required(role_required="Admin")
def get_all_transactions():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    query = """
    SELECT *
    FROM Transaction_History;
    """
    cursor.execute(query)
    transactions = cursor.fetchall()
    cursor.close()
    connection.close()

    return jsonify(transactions), 200


@app.route("/transactions/<int:user_id>", methods=["GET"])
@token_required(role_required="Admin")
def get_user_transactions(user_id):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
    SELECT id, user_id, old_wallet, new_wallet, description, date
    FROM Transaction_History
    WHERE user_id = %s
    ORDER BY date DESC;
    """
    cursor.execute(query, (user_id,))
    transactions = cursor.fetchall()

    cursor.close()
    connection.close()

    if not transactions:
        return (
            jsonify({"message": "No transactions found for the specified user."}),
            404,
        )

    return jsonify(transactions), 200


@app.route("/wallet", methods=["GET"])
@token_required(role_required="Player")
def get_Wallet():

    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_data = decode_token(token)
    if not user_data:
        return jsonify({"message": "Could not access user data."}), 401

    user_id = user_data.get("user_id")
    if not user_id:
        return jsonify({"message": "Could not access user id."}), 401

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
    SELECT wallet 
    FROM Wallets
    WHERE user_id = %s;
    """
    cursor.execute(query, (user_id,))
    transactions = cursor.fetchall()

    cursor.close()
    connection.close()

    if not transactions:
        return jsonify({"message": "No wallet found for the user."}), 404

    return jsonify(transactions), 200


@app.route("/refund", methods=["POST"])
@token_required(role_required="Admin")
def refund():
    data = request.get_json()

    users_to_refund = data.get("users", [])

    if not isinstance(users_to_refund, list) or not all(
        isinstance(user, dict) for user in users_to_refund
    ):
        return (
            jsonify(
                {
                    "message": "Invalid users list format. It must be a list of user objects."
                }
            ),
            400,
        )

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        for user in users_to_refund:
            user_id = user.get("user_id")
            amount = Decimal(user.get("amount", 0))

            if not user_id or amount <= 0:
                return (
                    jsonify(
                        {
                            "message": "Each user must have a valid user_id and a positive amount."
                        }
                    ),
                    400,
                )

            cursor.execute(
                "SELECT id, wallet FROM Wallets WHERE user_id = %s;", (user_id,)
            )
            wallet_data = cursor.fetchone()

            if not wallet_data:
                cursor.execute(
                    "INSERT INTO Wallets (user_id, wallet) VALUES (%s, %s);",
                    (user_id, 0.00),
                )
                connection.commit()
                cursor.execute(
                    "SELECT id, wallet FROM Wallets WHERE user_id = %s;", (user_id,)
                )
                wallet_data = cursor.fetchone()

            wallet_id, old_wallet = wallet_data
            new_wallet = old_wallet + amount

            cursor.execute(
                "UPDATE Wallets SET wallet = %s WHERE id = %s;", (new_wallet, wallet_id)
            )

            description = f"Refunded {amount} to wallet."
            cursor.execute(
                """
                INSERT INTO Transaction_History (wallet_id, user_id, old_wallet, new_wallet, description, date)
                VALUES (%s, %s, %s, %s, %s, NOW());
                """,
                (wallet_id, user_id, old_wallet, new_wallet, description),
            )

        connection.commit()

    except Exception as e:
        connection.rollback()
        return (
            jsonify(
                {
                    "message": "An error occurred while processing refunds.",
                    "error": str(e),
                }
            ),
            500,
        )

    finally:
        cursor.close()
        connection.close()

    return jsonify({"message": "Refunds processed successfully!"}), 200


@app.route("/add_currency", methods=["POST"])
@token_required(role_required="Admin")
def add_new_currency():
    data = request.get_json()

    if not data:
        return jsonify({"message": "Invalid or missing JSON payload."}), 400

    user_id = sanitize_input(data.get("user_id"))
    amount = sanitize_decimal(data.get("amount"))

    if not amount or amount <= 0:
        return jsonify({"message": "Invalid amount. Must be greater than zero."}), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT id, wallet FROM Wallets WHERE user_id = %s;", (user_id,))
        wallet_data = cursor.fetchone()

        if not wallet_data:
            cursor.execute(
                "INSERT INTO Wallets (user_id, wallet) VALUES (%s, %s);",
                (user_id, 0.00),
            )
            connection.commit()
            cursor.execute(
                "SELECT id, wallet FROM Wallets WHERE user_id = %s;", (user_id,)
            )
            wallet_data = cursor.fetchone()

        wallet_id, old_wallet = wallet_data
        new_wallet = old_wallet + amount

        cursor.execute(
            "UPDATE Wallets SET wallet = %s WHERE id = %s;", (new_wallet, wallet_id)
        )
        description = f"Added {amount} to wallet via currency addition."
        cursor.execute(
            """
            INSERT INTO Transaction_History (wallet_id, user_id, old_wallet, new_wallet, description, date)
            VALUES (%s, %s, %s, %s, %s, NOW());
            """,
            (wallet_id, user_id, old_wallet, new_wallet, description),
        )
        connection.commit()

    except Exception as e:
        connection.rollback()
        return (
            jsonify(
                {"message": "An error occurred while adding currency.", "error": str(e)}
            ),
            500,
        )

    finally:
        cursor.close()
        connection.close()

    return (
        jsonify({"message": f"{amount} added to user {user_id} wallet successfully!"}),
        200,
    )


if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5002,
        ssl_context=(
            "/run/secrets/https_currency_cert",
            "/run/secrets/https_currency_key",
        ),
    )
