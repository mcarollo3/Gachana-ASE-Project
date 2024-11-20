from flask import Flask, request, jsonify
import mysql.connector
import os
from decode_auth_token import decode_token, token_required

app = Flask(__name__)

# Get DB Connection
def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        database=os.environ.get("DB_NAME")
    )

# Visualizzare oggetti in vendita
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

# Pubblicare un oggetto in vendita
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

# Fare un'offerta
@app.route('/market/<int:user_id>/<int:gacha_id>/bid', methods=['POST'])
@token_required(role_required='Player')
def make_offer(user_id, gacha_id):
    data = request.get_json()
    offer_value = data.get('offer_value')

    connection = get_db_connection()
    cursor = connection.cursor()

    # Inserisce l'offerta
    query_offer = """
    INSERT INTO Offers (market_id, user_id, offer_value)
    SELECT Market.id, %s, %s
    FROM Market
    WHERE Market.gacha_id = %s AND Market.user_id != %s;
    """
    cursor.execute(query_offer, (user_id, offer_value, gacha_id, user_id))

    # Aggiorna l'offerta più alta sul mercato
    query_update_market = """
    UPDATE Market
    SET value_last_offer = %s
    WHERE gacha_id = %s;
    """
    cursor.execute(query_update_market, (offer_value, gacha_id))

    connection.commit()
    cursor.close()
    connection.close()
    
    return jsonify({"message": "Offer placed successfully."}), 201

# Accettare un'offerta
@app.route('/market/<int:user_id>/<int:gacha_id>/accept', methods=['POST'])
@token_required(role_required='Player')
def accept_offer(user_id, gacha_id):
    data = request.get_json()
    buyer_id = data.get('buyer_id')
    gacha_value = data.get('gacha_value')

    connection = get_db_connection()
    cursor = connection.cursor()

    # Ottiene l'offerta accettata x gacha
    query_offer = """
    SELECT Offers.user_id AS buyer_id, Offers.offer_value, Market.user_id AS seller_id
    FROM Offers
    JOIN Market ON Offers.market_id = Market.id
    WHERE Market.gacha_id = %s AND Offers.user_id = %s
    ORDER BY Offers.offer_value DESC
    LIMIT 1;
    """
    cursor.execute(query_offer, (gacha_id, buyer_id))
    offer = cursor.fetchone()

    if not offer:
        cursor.close()
        connection.close()
        return jsonify({"error": "Offer not found or already processed."}), 404

    # Inserisce la transazione
    query_transaction = """
    INSERT INTO Transaction_History (user_seller_id, user_buyer_id, gacha_value, id_gacha, date)
    VALUES (%s, %s, %s, %s, NOW());
    """
    cursor.execute(query_transaction, (offer['seller_id'], offer['buyer_id'], offer['offer_value'], gacha_id))

    # Rimuove l'oggetto dal mercato
    query_remove_market = """
    DELETE FROM Market WHERE gacha_id = %s;
    """
    cursor.execute(query_remove_market, (gacha_id,))

    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({"message": "Offer accepted and transaction completed."}), 200

# Visualizzare cronologia transazioni 
@app.route('/market/<int:user_id>/transactions', methods=['GET'])
@token_required(role_required='Player')
def get_transaction_history(user_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
    SELECT Transaction_History.id, Transaction_History.gacha_value, Transaction_History.date,
           Gacha.name AS gacha_name, Users.username AS buyer_name
    FROM Transaction_History
    JOIN Gacha ON Transaction_History.id_gacha = Gacha.id
    JOIN Users ON Transaction_History.user_buyer_id = Users.id
    WHERE Transaction_History.user_seller_id = %s OR Transaction_History.user_buyer_id = %s;
    """
    cursor.execute(query, (user_id, user_id))
    transactions = cursor.fetchall()

    cursor.close()
    connection.close()

    if not transactions:
        return jsonify({"error": "No transactions found for this user"}), 404

    return jsonify(transactions), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
