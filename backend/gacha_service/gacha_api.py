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

@app.route('/collection', methods=['GET'])
@token_required(role_required='Player')
def get_user_collection():
    
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_data = decode_token(token)
    if not user_data:
        return jsonify(), 401
    user_id = user_data.get('user_id')
    if not  user_id:
        return jsonify(), 401

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    query = """ 
    SELECT Gacha.id, Gacha.name, Gacha.description, Gacha.id_img, Gacha.rarity, Collection.quantity
    FROM Collection
    JOIN Gacha ON Collection.gacha_id = Gacha.id
    WHERE Collection.user_id=%s
    """
    cursor.execute(query, (user_id, ))
    user_collection = cursor.fetchall()
    cursor.close()
    connection.close()

    if not user_collection or user_collection is None:
        return jsonify([]), 200
    return jsonify(user_collection), 200

@app.route('/collection/<int:gacha_id>', methods=['GET']                )
@token_required(role_required='Player')
def get_user_gacha(gacha_id):

    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_data = decode_token(token)
    if not user_data:
        return jsonify(), 401
    user_id = user_data.get('user_id')
    if not  user_id:
        return jsonify(), 401

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    query = """
    SELECT Gacha.id, Gacha.name, Gacha.description, Gacha.id_img, Gacha.rarity
    FROM Collection
    JOIN Gacha ON Collection.gacha_id = Gacha.id
    WHERE Collection.user_id = %s AND Collection.gacha_id = %s;
    """
    cursor.execute(query, (user_id, gacha_id))
    user_gacha = cursor.fetchone()
    cursor.close()
    connection.close()

    if not user_gacha or user_gacha is None:
        return jsonify({"error": "Gacha not found or not owned by user."}), 404
    return jsonify(user_gacha), 200

@app.route('/collection/available', methods=['GET'])
@token_required(role_required='Player')
def get_available_gachas():

    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_data = decode_token(token)
    if not user_data:
        return jsonify(), 401
    user_id = user_data.get('user_id')
    if not  user_id:
        return jsonify(), 401

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    query = """
    SELECT Gacha.id, Gacha.name, Gacha.description, Gacha.id_img, Gacha.rarity
    FROM Gacha
    LEFT JOIN Collection ON Gacha.id = Collection.gacha_id AND Collection.user_id = %s 
    WHERE Collection.user_id IS NULL;
    """
    cursor.execute(query, (user_id, ))
    available_gacha = cursor.fetchall()
    cursor.close()
    connection.close()

    if not available_gacha or available_gacha is None:
        return jsonify({"message": "User owns every gacha."}), 200
    return jsonify(available_gacha), 200

@app.route('/collection/available/<int:gacha_id>', methods=['GET'])
@token_required(role_required='Player')
def get_available_gacha(gacha_id):

    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_data = decode_token(token)
    if not user_data:
        return jsonify(), 401
    user_id = user_data.get('user_id')
    if not  user_id:
        return jsonify(), 401

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    query = """
    SELECT Gacha.id, Gacha.name, Gacha.description, Gacha.id_img, Gacha.rarity
    FROM Gacha
    LEFT JOIN Collection ON Gacha.id = Collection.gacha_id AND Collection.user_id = %s
    WHERE Gacha.id = 2 AND Collection.user_id IS NULL;
    """
    cursor.execute(query, (user_id, ))
    available_gacha = cursor.fetchall()
    cursor.close()
    connection.close()

    if not available_gacha or available_gacha is None:
        return jsonify({"message": "User owns every gacha."}), 200
    return jsonify(available_gacha), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)