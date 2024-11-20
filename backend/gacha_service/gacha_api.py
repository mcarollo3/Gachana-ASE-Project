from flask import Flask, json, request, make_response, jsonify
import mysql.connector
import os
from decode_auth_token import decode_token, token_required
import random

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
        return jsonify({'message':'Could not access user data.'}), 401
    user_id = user_data.get('user_id')
    if not  user_id:
        return jsonify({'message':'Could not access user id.'}), 401

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    query = """ 
    SELECT Gacha.id, Gacha.name, Gacha.id_img, Collection.quantity
    FROM Collection
    JOIN Gacha ON Collection.gacha_id = Gacha.id    
    WHERE Collection.user_id=%s;
    """
    cursor.execute(query, (user_id, ))
    user_collection = cursor.fetchall()
    cursor.close()
    connection.close()

    if not user_collection or user_collection is None:
        return jsonify({'message':'User owns no gachas.'}), 200
    return jsonify(user_collection), 200

@app.route('/collection/<int:gacha_id>', methods=['GET']                )
@token_required(role_required='Player')
def get_user_gacha(gacha_id):

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
        return jsonify({'message':'Gacha not found or not owned by user.'}), 404
    return jsonify(user_gacha), 200

@app.route('/collection/available', methods=['GET'])
@token_required(role_required='Player')
def get_available_gachas():

    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_data = decode_token(token)
    if not user_data:
        return jsonify({'message':'Could not access user data.'}), 401
    user_id = user_data.get('user_id')
    if not user_id:
        return jsonify({'message':'Could not access user id.'}), 401

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    query = """
    SELECT Gacha.id, Gacha.name, Gacha.id_img
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
        return jsonify({'message': 'Could not access user data.'}), 401
    user_id = user_data.get('user_id')
    if not user_id:
        return jsonify({'message': 'Could not access user id.'}), 401

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    query = """
    SELECT Gacha.id, Gacha.name, Gacha.description, Gacha.id_img, Gacha.rarity
    FROM Gacha
    LEFT JOIN Collection ON Gacha.id = Collection.gacha_id AND Collection.user_id = %s
    WHERE Gacha.id = %s AND Collection.user_id IS NULL;
    """
    cursor.execute(query, (user_id, gacha_id))
    available_gacha = cursor.fetchone()  
    cursor.close()
    connection.close()

    if available_gacha is None:  
        return jsonify({"message": "User already owns this gacha."}), 200

    return jsonify(available_gacha), 200

@app.route('/collection/roll', methods=['POST'])     
@token_required(role_required='Player')
def roll_gacha():

    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_data = decode_token(token)
    if not user_data:
        return jsonify({'message':'Could not access user data.'}), 401
    user_id = user_data.get('user_id')
    if not user_id:
        return jsonify({'message':'Could not access user id.'}), 401
    
    gacha_id = random.randint(1, 20)

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    query = """
    SELECT EXISTS (
        SELECT 1
        FROM Collection
        WHERE user_id = %s AND gacha_id = %s
    ) AS owns;
    """
    cursor.execute(query, (user_id, gacha_id))
    owns_dict = cursor.fetchone()
    already_owned = int(owns_dict["owns"])

    if already_owned == 0:
        query="""
        INSERT INTO Collection (user_id, gacha_id, quantity)
        VALUES (%s, %s, 1);
        """
    else:
        query="""
        UPDATE Collection
        SET quantity = quantity + 1
        WHERE user_id = %s AND gacha_id = %s;
        """

    cursor.execute(query, (user_id, gacha_id))
    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({"message": "User successfully rolled gacha " + str(gacha_id) + "."}), 200

@app.route('/gachas', methods=['GET'])
@token_required(role_required='Admin')
def get_gachas():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    query = """
    SELECT *
    FROM Gacha;
    """
    cursor.execute(query)
    gachas = cursor.fetchall()
    cursor.close()
    connection.close()

    return jsonify(gachas), 200

@app.route('/gachas/<int:gacha_id>', methods=['GET'])
@token_required(role_required='Admin')
def get_gacha(gacha_id):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    query = """
    SELECT *
    FROM Gacha
    WHERE id = %s;
    """
    cursor.execute(query, (gacha_id, ))
    gacha = cursor.fetchall()
    cursor.close()
    connection.close()

    return jsonify(gacha), 200

@app.route('/gachas/update/<int:gacha_id>', methods=['PATCH'])     
@token_required(role_required='Admin')
def patch_gacha(gacha_id):

    data = request.get_json()

    if not data.get('name') and not data.get('rarity') and not data.get('description') and not data.get('id_img'):
        return jsonify({'message': 'No data provided for update.'}), 400

    name = data.get('name')
    rarity = data.get('rarity')
    description = data.get('description')
    id_img = data.get('id_img')

    query = "UPDATE Gacha SET "
    params = []

    if name:
        query += "name = %s, "
        params.append(name)
    if rarity:
        query += "rarity = %s, "
        params.append(rarity)
    if description:
        query += "description = %s, "
        params.append(description)
    if id_img:
        query += "id_img = %s, "
        params.append(id_img)

    query = query.rstrip(', ')

    query += " WHERE id = %s"
    params.append(gacha_id)

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(query, tuple(params))
    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({'message': 'Gacha modified successfully.'}), 200

@app.route('/gachas/add', methods=['POST'])
@token_required(role_required='Admin')  
def add_gacha():
    data = request.get_json()
    if not data:
        return jsonify({'message': 'Invalid request. JSON data is required.'}), 400

    name = data.get('name')
    description = data.get('description')
    id_img = data.get('id_img')
    rarity = data.get('rarity')

    if not name or not rarity:
        return jsonify({'message': 'Name and rarity are required fields.'}), 400

    if rarity not in ['Common', 'Uncommon', 'Rare', 'Super Rare', 'Legendary']:
        return jsonify({'message': f'Invalid rarity: {rarity}. Must be one of Common, Uncommon, Rare, Super Rare, Legendary.'}), 400

    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        query = """
        INSERT INTO Gacha (name, description, id_img, rarity)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (name, description, id_img, rarity))
        connection.commit()
        new_gacha_id = cursor.lastrowid
    except Exception as e:
        connection.rollback()
        return jsonify({'message': f'Error adding gacha: {str(e)}'}), 500
    finally:
        cursor.close()
        connection.close()

    return jsonify({'message': 'Gacha added successfully.', 'gacha_id': new_gacha_id}), 201


@app.route('/gachas/delete/<int:gacha_id>', methods=['DELETE'])
@token_required(role_required='Admin')  
def delete_gacha(gacha_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        query_users = """
        SELECT DISTINCT user_id
        FROM Collection
        WHERE gacha_id = %s
        """
        cursor.execute(query_users, (gacha_id,))
        users = cursor.fetchall()  
        user_ids = [user['user_id'] for user in users]  

        
        query_delete_collection = """
        DELETE FROM Collection
        WHERE gacha_id = %s
        """
        cursor.execute(query_delete_collection, (gacha_id,))

        query_delete_gacha = """
        DELETE FROM Gacha
        WHERE id = %s
        """
        cursor.execute(query_delete_gacha, (gacha_id,))

        connection.commit()

    except Exception as e:
        connection.rollback()  
        return jsonify({'message': f'Error deleting gacha: {str(e)}'}), 500
    finally:
        cursor.close()
        connection.close()

    return jsonify({
        'message': 'Gacha deleted successfully.',
        'removed_from_users': user_ids  
    }), 200
    # aggiungere un refound all'utente
  

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)