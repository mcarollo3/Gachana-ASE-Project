from flask import Flask, json, request, make_response, jsonify
import mysql.connector
import os
from decode_auth_token import decode_token, token_required

app = Flask(__name__)


def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        database=os.environ.get("DB_NAME")
    )

#see the object for sale in the market  if it is necessary 
@app.route('/market', methods=['GET'])
def get_market_items():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    query = """
    SELECT Market.id, Market.gacha_id, Gacha.name, Market.value_last_offer, Market.start_date, Market.end_date
    FROM Market
    JOIN Gacha ON Market.gacha_id = Gacha.id
    WHERE Market.end_date > NOW();
    """
    cursor.execute(query)
    market_items = cursor.fetchall()
    cursor.close()
    connection.close()
    
    return jsonify(market_items), 200

#put an item for sale?
@app.route('/market', methods=['POST'])
@token_required(role_required='Player')
def post_market_item():
    data = request.get_json()
    gacha_id = data.get('gacha_id')
    user_id = data.get('user_id')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    value = data.get('value')

    connection = get_db_connection()
    cursor = connection.cursor()
    query = """
    INSERT INTO Market (gacha_id, user_id, value_last_offer, start_date, end_date)
    VALUES (%s, %s, %s, %s, %s);
    """
    cursor.execute(query, (gacha_id, user_id, value, start_date, end_date))
    connection.commit()
    cursor.close()
    connection.close()
    
    return jsonify({"message": "Item listed for sale."}), 201



@app.route('/')
def home():
    return '<h1>Hello!</h1>'  



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)