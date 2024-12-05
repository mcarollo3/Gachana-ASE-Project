from flask import Flask, request, jsonify
import time
import mysql.connector
from mysql.connector import Error
import os
from decode_auth_token import decode_token, token_required
from datetime import datetime

from get_secrets import get_secret_value

from make_requests import make_request

app = Flask(__name__)
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("No SECRET_KEY set for Flask application")

CERT_FILE = "/run/secrets/https_market_cert"
KEY_FILE = "/run/secrets/https_market_key"
CURRENCY_URL = "https://currency_service:5002"
GACHA_URL = "https://gacha_service:5001"
USER_URL = "https://user_service:5000"

mock_add_currency = None
mock_check_and_deduct = None
mock_collection = None
mock_collection_add = None
mock_login = None
mock_refund = None
mock_remove = None

# Get DB Connection
def get_db_connection():
    ssl_ca = "/run/secrets/db_https_market_cert"
    ssl_cert = "/run/secrets/db_https_market_cert"
    ssl_key = "/run/secrets/db_https_market_key"

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

def sanitize_input(data, data_type):

    if data_type == "string":
        return str(data).strip() if data else None
    elif data_type == "int":
        try:
            return int(data)
        except ValueError:
            return None
    elif data_type == "float":
        try:
            return float(data)
        except ValueError:
            return None
    elif data_type == "date":
        try:
            return datetime.strptime(data, "%Y-%m-%d") if data else None
        except ValueError:
            return None
    return data

@app.route("/list", methods=["GET"])
@token_required(role_required=["Admin", "Player"])
def get_market_items():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query_get_expired_market_offers = """
    SELECT o.user_id, o.offer_value
    FROM Market m
    JOIN Offers o ON m.id = o.market_id
    WHERE m.end_date IS NOT NULL AND m.end_date < NOW();
    """
    cursor.execute(query_get_expired_market_offers)
    expired_market_offers = cursor.fetchall()

    offer_list = [
        {"userId": offer["user_id"], "amount": offer["offer_value"]}
        for offer in expired_market_offers
    ]

    if len(offer_list) > 0:
        if mock_login:
            adminLogin = mock_login()
        else:
            adminLogin = make_request(
                USER_URL + "/login",
                method="POST",
                data={"username": "admin", "psw": "gachana"},
                cert=(CERT_FILE, KEY_FILE),
            )

        if adminLogin.status_code != 200:
            return (
                jsonify(adminLogin.json()),
                adminLogin.status_code,
            )

        tokenAdmin = adminLogin.json().get("token")
        if mock_refund:
            refundUsers = mock_refund()
        else:
            refundUsers = make_request(
                CURRENCY_URL + "/refund",
                method="POST",
                data=offer_list,
                headers={
                    "Authorization": "Bearer " + tokenAdmin,
                    "Content-Type": "application/json",
                },
                cert=(CERT_FILE, KEY_FILE),
            )

        if refundUsers.status_code != 200:
            return (
                jsonify(refundUsers.json()),
                refundUsers.status_code,
            )

    query_delete_expired = """
    DELETE FROM Market
    WHERE end_date IS NOT NULL AND end_date < NOW();
    """
    cursor.execute(query_delete_expired)
    connection.commit()

    query_get_market_items = """
    SELECT * FROM Market;
    """
    cursor.execute(query_get_market_items)
    market_items = cursor.fetchall()

    cursor.close()
    connection.close()

    if len(market_items) > 0:
        return jsonify(market_items), 200
    else:
        return jsonify({"message": "No auctions available."}), 200

@app.route("/new-auction", methods=["POST"])
@token_required(role_required="Player")
def post_market_item():

    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_data = decode_token(token)
    if not user_data:
        return jsonify({"message": "Could not access user data."}), 401

    user_id = user_data.get("user_id")
    if not user_id:
        return jsonify({"message": "Could not access user id."}), 401

    data = request.get_json()
    gacha_id = sanitize_input(data.get("gacha_id"), "int")
    start_date = datetime.now()
    end_date = sanitize_input(data.get("end_date"), "date")
    init_value = sanitize_input(data.get("init_value"), "float")

    if not end_date:
        return jsonify({"message": "End date is required."}), 400

    try:

        if (end_date - start_date).days <= 1:
            return (
                jsonify({"message": "End date must be at least one day after today."}),
                400,
            )
    except ValueError:
        return jsonify({"message": "Invalid end date format. Use 'YYYY-MM-DD'."}), 400

    # Check if user has the gacha
    if mock_collection:
        hasChosenGacha = mock_collection()
    else:
        hasChosenGacha = make_request(
            GACHA_URL + f"/collection/{gacha_id}",
            method="GET",
            headers={
                "Authorization": "Bearer " + request.headers.get("Authorization", ""),
                "Content-Type": "application/json",
            },
            cert=(CERT_FILE, KEY_FILE),
        )

    if hasChosenGacha.status_code != 200:
        return (
            jsonify(hasChosenGacha.json()),
            hasChosenGacha.status_code,
        )

    connection = get_db_connection()
    cursor = connection.cursor()
    query = """
    INSERT INTO Market (gacha_id, user_id, init_value, value_last_offer, start_date, end_date)
    VALUES (%s, %s, %s, %s, %s, %s);
    """
    cursor.execute(query, (gacha_id, user_id, init_value, 0, start_date, end_date))
    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({"message": "Item listed for sale."}), 201


@app.route("/new-bid", methods=["POST"])
@token_required(role_required="Player")
def make_offer():

    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_data = decode_token(token)
    if not user_data:
        return jsonify({"message": "Could not access user data."}), 401

    user_id = user_data.get("user_id")
    if not user_id:
        return jsonify({"message": "Could not access user id."}), 401

    data = request.get_json()
    market_id = sanitize_input(data.get("market_id"), "int")
    offer_value = sanitize_input(data.get("offer_value"), "float")

    if not market_id or not offer_value:
        return jsonify({"message": "Market ID and offer value are required."}), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    query_check_creator = """
    SELECT user_id 
    FROM Market 
    WHERE id = %s;
    """
    cursor.execute(query_check_creator, (market_id,))
    result = cursor.fetchone()

    if not result:
        return jsonify({"message": "Market not found."}), 404

    market_creator_id = result[0]
    if user_id == market_creator_id:
        return jsonify({"message": "You cannot bid on your own auction."}), 403

    if mock_check_and_deduct:
        hasEnoughWallet = mock_check_and_deduct()
    else:
        hasEnoughWallet = make_request(
            CURRENCY_URL + "/check_and_deduct",
            method="POST",
            data={"amount": offer_value},
            headers={
                "Authorization": "Bearer " + request.headers.get("Authorization", ""),
                "Content-Type": "application/json",
            },
            cert=(CERT_FILE, KEY_FILE),
        )

    if hasEnoughWallet.status_code != 200:
        return (
            jsonify(hasEnoughWallet.json()),
            hasEnoughWallet.status_code,
        )

    query_check_offer = """
    SELECT id, offer_value 
    FROM Offers 
    WHERE market_id = %s AND user_id = %s;
    """
    cursor.execute(query_check_offer, (market_id, user_id))
    existing_offer = cursor.fetchone()

    if existing_offer:
        query_update_offer = """
        UPDATE Offers
        SET offer_value = %s
        WHERE id = %s;
        """
        cursor.execute(query_update_offer, (offer_value, existing_offer[0]))
    else:
        query_insert_offer = """
        INSERT INTO Offers (market_id, user_id, offer_value) 
        VALUES (%s, %s, %s);
        """
        cursor.execute(query_insert_offer, (market_id, user_id, offer_value))

    query_update_market = """
    UPDATE Market
    SET value_last_offer = %s
    WHERE id = %s;
    """
    cursor.execute(query_update_market, (offer_value, market_id))

    connection.commit()
    cursor.close()
    connection.close()

    return (
        jsonify(
            {
                "message": (
                    "Offer updated successfully."
                    if existing_offer
                    else "Offer placed successfully."
                )
            }
        ),
        200,
    )


@app.route("/<int:market_id>/offers", methods=["GET"])
@token_required(role_required=["Admin", "Player"])
def get_offers(market_id):

    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_data = decode_token(token)
    if not user_data:
        return jsonify({"message": "Could not access user data."}), 401

    user_id = user_data.get("user_id")
    role = user_data.get("role")
    if not user_id:
        return jsonify({"message": "Could not access user id."}), 401

    connection = get_db_connection()
    cursor = connection.cursor()

    query_check_creator = """
    SELECT user_id 
    FROM Market 
    WHERE id = %s;
    """
    cursor.execute(query_check_creator, (market_id,))
    result = cursor.fetchone()

    if not result:
        return jsonify({"message": "Market not found."}), 404

    market_creator_id = result[0]
    if user_id != market_creator_id and role != "Admin":
        return (
            jsonify(
                {"message": "You are not authorized to view offers for this auction."}
            ),
            403,
        )

    query_get_offers = """
    SELECT id, user_id, offer_value 
    FROM Offers 
    WHERE market_id = %s;
    """
    cursor.execute(query_get_offers, (market_id,))
    offers = cursor.fetchall()

    offers_list = [
        {"offer_id": row[0], "user_id": row[1], "offer_value": float(row[2])}
        for row in offers
    ]

    cursor.close()
    connection.close()

    return jsonify({"market_id": market_id, "offers": offers_list}), 200


@app.route("/accept", methods=["POST"])
@token_required(role_required="Player")
def accept_offer():

    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_data = decode_token(token)
    if not user_data:
        return jsonify({"message": "Could not access user data."}), 401

    seller_id = user_data.get("user_id")
    if not seller_id:
        return jsonify({"message": "Could not access user id."}), 401

    data = request.get_json()
    market_id = sanitize_input(data.get("market_id"), "int")
    buyer_id = sanitize_input(data.get("buyer_id"), "int")

    if not market_id or not buyer_id:
        return jsonify({"message": "Market ID and buyer ID are required."}), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    query_check_market = """
    SELECT id, gacha_id 
    FROM Market 
    WHERE id = %s AND user_id = %s;
    """
    cursor.execute(query_check_market, (market_id, seller_id))
    market = cursor.fetchone()

    if not market:
        return (
            jsonify(
                {
                    "message": "Market not found or you are not the owner of this auction."
                }
            ),
            403,
        )

    query_check_offers = """
    SELECT COUNT(*) 
    FROM Offers 
    WHERE market_id = %s;
    """
    cursor.execute(query_check_offers, (market_id,))
    offer_count = cursor.fetchone()[0]

    if offer_count == 0:
        return jsonify({"message": "No offers found for this market."}), 404

    gacha_id = market[1]

    query_get_offer = """
    SELECT id, offer_value 
    FROM Offers 
    WHERE market_id = %s AND user_id = %s;
    """
    cursor.execute(query_get_offer, (market_id, buyer_id))
    accepted_offer = cursor.fetchone()

    if not accepted_offer:
        return jsonify({"message": "Offer not found for the specified buyer."}), 404

    offer_id, offer_value = accepted_offer

    if mock_login:
        adminLogin = mock_login()
    else:
        adminLogin = make_request(
            USER_URL + "/login",
            method="POST",
            data={"username": "admin", "psw": "gachana"},
            cert=(CERT_FILE, KEY_FILE),
        )

    if adminLogin.status_code != 200:
        return (
            jsonify(adminLogin.json()),
            adminLogin.status_code,
        )

    tokenAdmin = adminLogin.json().get("token")

    query_get_rejected_offers = """
    SELECT user_id, offer_value 
    FROM Offers 
    WHERE market_id = %s AND user_id != %s;
    """
    cursor.execute(query_get_rejected_offers, (market_id, buyer_id))
    rejected_offers = cursor.fetchall()

    if len(rejected_offers) > 0:
        if mock_refund:
            refundUsers = mock_refund()
        else:
            refundUsers = make_request(
                CURRENCY_URL + "/refund",
                method="POST",
                data=[
                    {"user_id": user_id, "amount": value}
                    for user_id, value in rejected_offers
                ],
                headers={
                    "Authorization": "Bearer " + tokenAdmin,
                    "Content-Type": "application/json",
                },
                cert=(CERT_FILE, KEY_FILE),
            )

        if refundUsers.status_code != 200:
            return (
                jsonify(refundUsers.json()),
                refundUsers.status_code,
            )

        query_delete_rejected_offers = """
        DELETE FROM Offers 
        WHERE market_id = %s AND user_id != %s;
        """
        cursor.execute(query_delete_rejected_offers, (market_id, buyer_id))

    query_insert_history = """
    INSERT INTO Market_History (user_seller_id, user_buyer_id, gacha_value, id_gacha, date)
    SELECT %s, %s, %s, gacha_id, NOW()
    FROM Market
    WHERE id = %s;
    """
    cursor.execute(query_insert_history, (seller_id, buyer_id, offer_value, market_id))

    query_delete_market = """
    DELETE FROM Market 
    WHERE id = %s;
    """
    cursor.execute(query_delete_market, (market_id,))

    connection.commit()
    cursor.close()
    connection.close()

    if mock_collection_add:
        addGachaToBuyer = mock_collection_add
    else:
        addGachaToBuyer = make_request(
            GACHA_URL + "/collection/add",
            method="POST",
            data={"user_id": buyer_id, "gacha_id": gacha_id},
            headers={
                "Authorization": "Bearer " + tokenAdmin,
                "Content-Type": "application/json",
            },
            cert=(CERT_FILE, KEY_FILE),
        )

    if addGachaToBuyer.status_code != 200:
        return (
            jsonify(addGachaToBuyer.json()),
            addGachaToBuyer.status_code,
        )

    if mock_remove:
        removeGachaFromSeller = mock_remove()
    else:
        removeGachaFromSeller = make_request(
            GACHA_URL + "/remove",
            method="POST",
            data={"user_id": buyer_id, "gacha_id": gacha_id},
            headers={
                "Authorization": "Bearer " + tokenAdmin,
                "Content-Type": "application/json",
            },
            cert=(CERT_FILE, KEY_FILE),
        )

    if removeGachaFromSeller.status_code != 200:
        return (
            jsonify(removeGachaFromSeller.json()),
            removeGachaFromSeller.status_code,
        )

    if mock_add_currency:
        addCurrencyToSeller = mock_add_currency()
    else:
        addCurrencyToSeller = make_request(
            CURRENCY_URL + "/add_currency",
            method="POST",
            data={"user_id": seller_id, "amount": float(offer_value)},
            headers={
                "Authorization": f"Bearer {tokenAdmin}",
            },
            cert=(CERT_FILE, KEY_FILE),
        )

    if addCurrencyToSeller.status_code != 200:
        try:
            response_text = addCurrencyToSeller.json()
        except ValueError:
            response_text = addCurrencyToSeller.text
        return (
            jsonify({"message": "Failed to add currency", "details": response_text}),
            addCurrencyToSeller.status_code,
        )

    return (
        jsonify(
            {
                "message": "Offer accepted successfully.",
            }
        ),
        200,
    )


@app.route("/history", methods=["GET"])
@token_required(role_required="Player")
def get_transaction_history():

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
    FROM Market_History
    WHERE user_seller_id = %s
        OR user_buyer_id = %s;
    """
    cursor.execute(query, (user_id, user_id))
    transactions = cursor.fetchall()

    cursor.close()
    connection.close()

    if not transactions:
        return jsonify({"error": "No market history found for this user"}), 404

    return jsonify(transactions), 200


# Admin


@app.route("/auction-details/<int:market_id>", methods=["GET"])
@token_required(role_required="Admin")
def get_auction_details(market_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    query_get_market = """
    SELECT id, gacha_id, user_id, init_value, value_last_offer, start_date, end_date
    FROM Market
    WHERE id = %s;
    """
    cursor.execute(query_get_market, (market_id,))
    market = cursor.fetchone()

    if not market:
        return jsonify({"message": "Market not found."}), 404

    query_get_offers = """
    SELECT id, user_id, offer_value
    FROM Offers
    WHERE market_id = %s;
    """
    cursor.execute(query_get_offers, (market_id,))
    offers = cursor.fetchall()

    market_details = {
        "market_id": market[0],
        "gacha_id": market[1],
        "user_id": market[2],
        "initial_value": str(market[3]),
        "last_offer_value": str(market[4]),
        "start_date": market[5].strftime("%Y-%m-%d"),
        "end_date": market[6].strftime("%Y-%m-%d") if market[6] else None,
    }

    offers_details = [
        {"offer_id": offer[0], "user_id": offer[1], "offer_value": str(offer[2])}
        for offer in offers
    ]

    connection.close()

    return (
        jsonify({"market_details": market_details, "current_offers": offers_details}),
        200,
    )


@app.route("/update-auction/<int:market_id>", methods=["PATCH"])
@token_required(role_required="Admin")
def update_auction(market_id):
    data = request.get_json()

    init_value = sanitize_input(data.get("init_value"), "float")
    value_last_offer = sanitize_input(data.get("value_last_offer"), "float")
    start_date = sanitize_input(data.get("start_date"), "date")
    end_date = sanitize_input(data.get("end_date"), "date")

    if not (init_value and start_date):
        return jsonify({"message": "Initial value and start date are required."}), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    query_check_market = """
    SELECT id
    FROM Market
    WHERE id = %s;
    """
    cursor.execute(query_check_market, (market_id,))
    market = cursor.fetchone()

    if not market:
        return jsonify({"message": "Market not found."}), 404

    query_update_market = """
    UPDATE Market
    SET init_value = %s,
        value_last_offer = %s,
        start_date = %s,
        end_date = %s
    WHERE id = %s;
    """
    cursor.execute(
        query_update_market,
        (init_value, value_last_offer, start_date, end_date, market_id),
    )

    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({"message": "Auction updated successfully."}), 200


@app.route("/history/all", methods=["GET"])
@token_required(role_required="Admin")
def get_market_history():
    connection = get_db_connection()
    cursor = connection.cursor()

    query_get_market_history = """
    SELECT *
    FROM Market_History;
    """
    cursor.execute(query_get_market_history)
    market_history = cursor.fetchall()
    cursor.close()
    connection.close()

    if len(market_history) > 0:
        return jsonify(market_history), 200
    else:
        return jsonify({"message": "There is not a market history."}), 200


if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5003,
        ssl_context=("/run/secrets/https_market_cert", "/run/secrets/https_market_key"),
    )
