from flask import Flask, json, request, make_response, jsonify
import mysql.connector
import os
from decode_auth_token import decode_token, token_required
from decimal import Decimal

app = Flask(__name__)
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("No SECRET_KEY set for Flask application")

# Get Connection DB
def get_db_connection():
    ssl_ca = "/run/secrets/db_https_currency_cert"
    ssl_cert = "/run/secrets/db_https_currency_cert"
    ssl_key = "/run/secrets/db_https_currency_key"

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

def simulate_payment(card_number, expiry_date, cvv):
    if len(card_number) == 16 and len(expiry_date) == 5 and len(cvv) == 3:
        return True
    return False

@app.route('/buy_currency', methods=['PATCH'])
@token_required(role_required='Player')
def add_funds():
    
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_data = decode_token(token)
    if not user_data:
        return jsonify({'message':'Could not access user data.'}), 401
    user_id = user_data.get('user_id')
    if not user_id:
        return jsonify({'message':'Could not access user id.'}), 401

    data = request.get_json()
    
    amount = Decimal(data.get('amount')) 
    card_number = data.get('card_number')
    expiry_date = data.get('expiry_date')
    cvv = data.get('cvv')

    if not amount or amount <= 0:
        return jsonify({'message': 'Invalid amount. Must be greater than zero.'}), 400

    if not all([card_number, expiry_date, cvv]):
        return jsonify({'message': 'Invalid card details. All fields are required.'}), 400

  
    payment_successful = simulate_payment(card_number, expiry_date, cvv)
    if not payment_successful:
        return jsonify({'message': 'Payment failed. Please check your card details.'}), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT id, wallet FROM Wallets WHERE user_id = %s;", (user_id,))
        wallet_data = cursor.fetchone()

        if not wallet_data:
            cursor.execute(
                "INSERT INTO Wallets (user_id, wallet) VALUES (%s, %s);",
                (user_id, 0.00)
            )
            connection.commit()  
            cursor.execute("SELECT id, wallet FROM Wallets WHERE user_id = %s;", (user_id,))
            wallet_data = cursor.fetchone()

        wallet_id, old_wallet = wallet_data
        new_wallet = old_wallet + amount

        cursor.execute(
            "UPDATE Wallets SET wallet = %s WHERE id = %s;",
            (new_wallet, wallet_id)
        )

        description = f"Added {amount} to wallet via card payment."
        cursor.execute(
            """
            INSERT INTO Transaction_History (wallet_id, user_id, old_wallet, new_wallet, description, date)
            VALUES (%s, %s, %s, %s, %s, NOW());
            """,
            (wallet_id, user_id, old_wallet, new_wallet, description)
        )

        connection.commit()

    except Exception as e:
        connection.rollback()
        return jsonify({'message': 'An error occurred while processing the transaction.', 'error': str(e)}), 500

    finally:
        cursor.close()
        connection.close()

    return jsonify({'message': f'{amount} added to your wallet successfully!'}), 200

@app.route('/transactions', methods=['GET'])
@token_required(role_required='Player')
def get_transactions():

    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_data = decode_token(token)
    if not user_data:
        return jsonify({'message': 'Could not access user data.'}), 401

    user_id = user_data.get('user_id')
    if not user_id:
        return jsonify({'message': 'Could not access user id.'}), 401

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
        return jsonify({'message': 'No transactions found for the user.'}), 404

    return jsonify(transactions), 200

@app.route('/transactions/list', methods=['GET'])
@token_required(role_required='Admin')
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

@app.route('/transactions/<int:user_id>', methods=['GET'])
@token_required(role_required='Admin')
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
        return jsonify({'message': 'No transactions found for the specified user.'}), 404

    return jsonify(transactions), 200


# Market Function
@app.route('/wallet', methods=['GET'])
@token_required(role_required='Player')
def get_Wallet():

    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_data = decode_token(token)
    if not user_data:
        return jsonify({'message': 'Could not access user data.'}), 401

    user_id = user_data.get('user_id')
    if not user_id:
        return jsonify({'message': 'Could not access user id.'}), 401

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
        return jsonify({'message': 'No wallet found for the user.'}), 404

    return jsonify(transactions), 200

@app.route('/spend_currency', methods=['PATCH'])
@token_required(role_required='Player')
def spend_funds():

    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_data = decode_token(token)
    if not user_data:
        return jsonify({'message':'Could not access user data.'}), 401
    user_id = user_data.get('user_id')
    if not user_id:
        return jsonify({'message':'Could not access user id.'}), 401

    data = request.get_json()
    amount = Decimal(data.get('amount'))  

    if not amount or amount <= 0:
        return jsonify({'message': 'Invalid amount. Must be greater than zero.'}), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT id, wallet FROM Wallets WHERE user_id = %s;", (user_id,))
        wallet_data = cursor.fetchone()

        if not wallet_data:
            return jsonify({'message': 'Wallet not found for the user.'}), 404

        wallet_id, old_wallet = wallet_data

        if old_wallet < amount:
            return jsonify({'message': 'Insufficient funds in wallet.'}), 400

        
        new_wallet = old_wallet - amount

        cursor.execute(
            "UPDATE Wallets SET wallet = %s WHERE id = %s;",
            (new_wallet, wallet_id)
        )

        description = f"Spent {amount} from wallet for an auction."
        cursor.execute(
            """
            INSERT INTO Transaction_History (wallet_id, user_id, old_wallet, new_wallet, description, date)
            VALUES (%s, %s, %s, %s, %s, NOW());
            """,
            (wallet_id, user_id, old_wallet, new_wallet, description)
        )

        connection.commit()

    except Exception as e:
        connection.rollback()
        return jsonify({'message': 'An error occurred while processing the transaction.', 'error': str(e)}), 500

    finally:
        cursor.close()
        connection.close()

    return jsonify({'message': f'{amount} deducted from your wallet successfully!'}), 200


@app.route('/refund', methods=['POST'])
def refund():
    data = request.get_json()

    token = data.get('token')
    if not token:
        return jsonify({'message': 'Token is required.'}), 400

    try:
        decoded_data = decode_token(token)  
        refund_data = decoded_data.get('dict', [])  
    except Exception as e:
        return jsonify({'message': 'Invalid token.', 'error': str(e)}), 400

    if not isinstance(refund_data, list) or not all(isinstance(item, dict) for item in refund_data):
        return jsonify({'message': 'Invalid refund data format. Expected a list of dictionaries.'}), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        for refund_item in refund_data:
            user_id = refund_item.get('user_id')
            offer_value = Decimal(refund_item.get('offer_value', "0.00"))

            if not user_id or offer_value <= 0:
                return jsonify({'message': 'Invalid refund data. Each item must have a valid user_id and positive offer_value.'}), 400

            cursor.execute("SELECT id, wallet FROM Wallets WHERE user_id = %s;", (user_id,))
            wallet_data = cursor.fetchone()

            if not wallet_data:
                cursor.execute(
                    "INSERT INTO Wallets (user_id, wallet) VALUES (%s, %s);",
                    (user_id, 0.00)
                )
                connection.commit()
                cursor.execute("SELECT id, wallet FROM Wallets WHERE user_id = %s;", (user_id,))
                wallet_data = cursor.fetchone()

            wallet_id, old_wallet = wallet_data

            new_wallet = old_wallet + offer_value

            cursor.execute(
                "UPDATE Wallets SET wallet = %s WHERE id = %s;",
                (new_wallet, wallet_id)
            )

            description = f"Refunded {offer_value} to wallet due to rejected offer."
            cursor.execute(
                """
                INSERT INTO Transaction_History (wallet_id, user_id, old_wallet, new_wallet, description, date)
                VALUES (%s, %s, %s, %s, %s, NOW());
                """,
                (wallet_id, user_id, old_wallet, new_wallet, description)
            )

        connection.commit()

    except Exception as e:
        connection.rollback()
        return jsonify({'message': 'An error occurred while processing refunds.', 'error': str(e)}), 500

    finally:
        cursor.close()
        connection.close()

    return jsonify({'message': 'Refunds processed successfully!'}), 200


@app.route('/add_currency', methods=['POST'])
def add_new_currency():
    data = request.get_json()

    token = data.get('token')
    if not token:
        return jsonify({'message': 'Token is required.'}), 400

    try:
        decoded_data = decode_token(token)
    except Exception as e:
        return jsonify({'message': 'Invalid token.', 'error': str(e)}), 400

    user_id = decoded_data.get('userId')
    amount = Decimal(decoded_data.get('amount', 0))

    if not user_id or amount <= 0:
        return jsonify({'message': 'Invalid token data. userId and amount must be valid.'}), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT id, wallet FROM Wallets WHERE user_id = %s;", (user_id,))
        wallet_data = cursor.fetchone()

        if not wallet_data:
            cursor.execute(
                "INSERT INTO Wallets (user_id, wallet) VALUES (%s, %s);",
                (user_id, 0.00)
            )
            connection.commit()
            cursor.execute("SELECT id, wallet FROM Wallets WHERE user_id = %s;", (user_id,))
            wallet_data = cursor.fetchone()

        wallet_id, old_wallet = wallet_data

        new_wallet = old_wallet + amount

        cursor.execute(
            "UPDATE Wallets SET wallet = %s WHERE id = %s;",
            (new_wallet, wallet_id)
        )

        description = f"Added {amount} to wallet via currency addition."
        cursor.execute(
            """
            INSERT INTO Transaction_History (wallet_id, user_id, old_wallet, new_wallet, description, date)
            VALUES (%s, %s, %s, %s, %s, NOW());
            """,
            (wallet_id, user_id, old_wallet, new_wallet, description)
        )

        connection.commit()

    except Exception as e:
        connection.rollback()
        return jsonify({'message': 'An error occurred while adding currency.', 'error': str(e)}), 500

    finally:
        cursor.close()
        connection.close()

    return jsonify({'message': f'{amount} added to user {user_id} wallet successfully!'}), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002, ssl_context=('/run/secrets/https_currency_cert', '/run/secrets/https_currency_key'))