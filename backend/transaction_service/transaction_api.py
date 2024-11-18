from flask import Flask, json, request, make_response, jsonify
import mysql.connector
import os
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

@app.route('/my_transactions/', methods=['GET'])
@token_required(role_required='Player')
def get_transactions(user_id):

    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_data = decode_token(token)
    if not user_data:
        return jsonify({'message':'Could not access user data.'}), 401
    user_id = user_data.get('user_id')
    if not  user_id:
        return jsonify({'message':'Could not access user id.'}), 401

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    query = """
    SELECT EXISTS (
        SELECT 1 
        FROM Transaction_History
        WHERE user_seller_id = %s
        OR user_buyer_id = %s
    );
    """
    cursor.execute(query, (user_id, user_id ))
    exists_dict = cursor.fetchone()
    exists = int(exists_dict["EXISTS"])

    if not exists:
        return jsonify({'message':'User not found.'}), 404

    query = """
    SELECT * 
    FROM Transaction_History
    WHERE user_seller_id = %s
        OR user_buyer_id = %s;
    """
    cursor.execute(query, (user_id, user_id))
    transactions = cursor.fetchall()
    cursor.close()
    connection.close()

    return jsonify(transactions), 200

@app.route('/all/', methods=['GET'])
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

@app.route('/user/<int:user_id>', methods=['GET'])
@token_required(role_required='Admin')
def get_user_transactions(user_id):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    query = """
    SELECT EXISTS (
        SELECT 1 
        FROM Transaction_History
        WHERE user_seller_id = %s OR user_buyer_id = %s
    ) AS result;
    """
    cursor.execute(query, (user_id, user_id))
    exists_dict = cursor.fetchone()
    exists = int(exists_dict["result"])     

    if not exists:
        return jsonify({'message':'User not found.'}), 404

    query = """
    SELECT * 
    FROM Transaction_History
    WHERE user_seller_id = %s
        OR user_buyer_id = %s;
    """
    cursor.execute(query, (user_id, user_id))
    transactions = cursor.fetchall()
    cursor.close()
    connection.close()

    return jsonify(transactions), 200

@app.route('/trans/<int:user_id>/<int:transaction_id>', methods=['GET'])
@token_required(role_required='Admin')
def get_this_transaction(user_id, transaction_id):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    query = """
    SELECT EXISTS (
        SELECT 1 
        FROM Transaction_History
        WHERE user_seller_id = %s
        OR user_buyer_id = %s
    );
    """
    cursor.execute(query, (user_id, user_id))
    exists = cursor.fetchone()[0]

    if not exists:
        return jsonify({'message':'User not found.'}), 404

    query = """
    SELECT * 
    FROM Transaction_History
    WHERE id = %s
        AND (user_seller_id = %s OR user_buyer_id = %s);
    """
    cursor.execute(query, (transaction_id, user_id, user_id))
    transaction = cursor.fetchall()
    cursor.close()
    connection.close()

    if not transaction:
        return jsonify({'message':'Transaction not found.'}), 404
    return jsonify(transaction), 200

@app.route('/add/', methods=['POST'])
@token_required(role_required='Admin')
def add_transaction():

    data = request.get_json()

    if not data.get('user_seller_id') and not data.get('user_buyer_id') and not data.get('gacha_value') and not data.get('id_gacha') and not data.get('date'):
        return jsonify({'message': 'No data provided for transaction.'}), 400

    user_seller_id = data.get('user_seller_id')
    user_buyer_id = data.get('user_buyer_id')
    gacha_value = data.get('gacha_value')
    id_gacha = data.get('id_gacha')
    date = data.get('date')

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    query = """
    INSERT INTO Transaction_History (user_seller_id, user_buyer_id, gacha_value, id_gacha, date)
    VALUES (%s, %s, %s, %s, %s)
    """

    cursor.execute(query, (user_seller_id, user_buyer_id, gacha_value, id_gacha, date))
    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({'message':'Transaction successfully added.'}), 200  

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)