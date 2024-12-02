from flask import Flask, json, request, make_response, jsonify, send_file
import mysql.connector
import os
from decode_auth_token import decode_token, token_required
from get_secrets import get_secret_value
import random
import requests
from io import BytesIO


CERT_FILE = "/run/secrets/https_gacha_cert"
KEY_FILE = "/run/secrets/https_gacha_key"
CURRENCY_URL = "https://currency_service:5002"


app = Flask(__name__)
SECRET_KEY = get_secret_value(os.environ.get("SECRET_KEY"))
if not SECRET_KEY:
    raise ValueError("No SECRET_KEY set for Flask application")


# Get Connection DB
def get_db_connection():
    ssl_ca = "/run/secrets/db_https_gacha_cert"
    ssl_cert = "/run/secrets/db_https_gacha_cert"
    ssl_key = "/run/secrets/db_https_gacha_key"

    return mysql.connector.connect(
        host=os.environ.get("DB_HOST"),
        user=get_secret_value(os.environ.get("DB_USER")),
        password=get_secret_value(os.environ.get("DB_PASSWORD")),
        database=os.environ.get("DB_NAME"),
        ssl_ca=ssl_ca,
        ssl_cert=ssl_cert,
        ssl_key=ssl_key,
    )


def insert_image(cursor, image_path, image_name):
    with open(image_path, "rb") as file:
        binary_data = file.read()
    query = "INSERT INTO Images (name, data) VALUES (%s, %s)"
    cursor.execute(query, (image_name, binary_data))


def populate_images():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    base_dir = "/app/gachas"
    subfolders = ["common", "uncommon", "rare", "superare", "legendary"]

    for folder in subfolders:
        folder_path = os.path.join(base_dir, folder)
        if os.path.isdir(folder_path):
            for img_name in os.listdir(folder_path):
                if img_name.endswith(".png"):
                    img_path = os.path.join(folder_path, img_name)
                    insert_image(cursor, img_path, img_name.replace(".png", ""))

    connection.commit()
    cursor.close()
    connection.close()


populate_images()


@app.route("/image/<string:image_name>", methods=["GET"])
def get_image(image_name):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        query = "SELECT data FROM Images WHERE name = %s"
        cursor.execute(query, (image_name,))
        image_data = cursor.fetchone()

        cursor.nextset()

        if not image_data:
            cursor.close()
            connection.close()
            return jsonify({"error": "Image not found"}), 404

        return send_file(BytesIO(image_data["data"]), mimetype="image/png")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        connection.close()


@app.route("/collection", methods=["GET"])
@token_required(role_required="Player")
def get_user_collection():

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
    SELECT Gacha.name, Gacha.name_img, Gacha.rarity, Collection.quantity
    FROM Collection
    JOIN Gacha ON Collection.gacha_id = Gacha.id    
    WHERE Collection.user_id=%s;
    """
    cursor.execute(query, (user_id,))
    user_collection = cursor.fetchall()
    cursor.close()
    connection.close()

    if not user_collection or user_collection is None:
        return jsonify({"message": "User owns no gachas."}), 200
    return jsonify(user_collection), 200


@app.route("/collection/<int:gacha_id>", methods=["GET"])
@token_required(role_required="Player")
def get_user_gacha(gacha_id):

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
    SELECT  Gacha.name, Gacha.description, Gacha.rarity
    FROM Collection
    JOIN Gacha ON Collection.gacha_id = Gacha.id
    WHERE Collection.user_id = %s AND Collection.gacha_id = %s;
    """
    cursor.execute(query, (user_id, gacha_id))
    user_gacha = cursor.fetchone()
    cursor.close()
    connection.close()

    if not user_gacha or user_gacha is None:
        return jsonify({"message": "Gacha not found or not owned by user."}), 404
    return jsonify(user_gacha), 200


@app.route("/collection/available", methods=["GET"])
@token_required(role_required="Player")
def get_available_gachas():

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
    SELECT Gacha.name, Gacha.rarity
    FROM Gacha
    LEFT JOIN Collection ON Gacha.id = Collection.gacha_id AND Collection.user_id = %s 
    WHERE Collection.user_id IS NULL;
    """
    cursor.execute(query, (user_id,))
    available_gacha = cursor.fetchall()
    cursor.close()
    connection.close()

    if not available_gacha or available_gacha is None:
        return jsonify({"message": "User owns every gacha."}), 200
    return jsonify(available_gacha), 200


@app.route("/collection/available/<int:gacha_id>", methods=["GET"])
@token_required(role_required="Player")
def get_available_gacha(gacha_id):
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
    SELECT Gacha.name, Gacha.description, Gacha.name_img, Gacha.rarity
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


@app.route("/roll", methods=["POST"])
@token_required(role_required="Player")
def roll_gacha():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    hasEnoughWallet = requests.post(
        CURRENCY_URL + "/check_and_deduct",
        json={"amount": 500},
        headers={
            "Authorization": "Bearer " + request.headers.get("Authorization", ""),
            "Content-Type": "application/json",
        },
        cert=(CERT_FILE, KEY_FILE),
        verify=False,
    )

    if hasEnoughWallet.status_code == 200:
        user_data = decode_token(token)
        if not user_data:
            return jsonify({"message": "Could not access user data."}), 401
        user_id = user_data.get("user_id")
        if not user_id:
            return jsonify({"message": "Could not access user id."}), 401

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
            query = """
            INSERT INTO Collection (user_id, gacha_id, quantity)
            VALUES (%s, %s, 1);
            """
        else:
            query = """
            UPDATE Collection
            SET quantity = quantity + 1
            WHERE user_id = %s AND gacha_id = %s;
            """
        cursor.execute(query, (user_id, gacha_id))
        connection.commit()

        query = "SELECT * FROM Gacha WHERE id = %s"
        cursor.execute(query, (gacha_id,))
        gacha = cursor.fetchone()

        if not gacha:
            cursor.close()
            connection.close()
            return jsonify({"message": "Gacha not found."}), 404

        cursor.close()
        connection.close()

        return (
            jsonify(
                {
                    "message": f"You successfully rolled gacha {gacha['name']}!",
                    "gacha_info": {
                        "name": gacha["name"],
                        "description": gacha["description"],
                        "rarity": gacha["rarity"],
                    },
                }
            ),
            200,
        )
    else:
        return (
            jsonify(hasEnoughWallet.json()),
            hasEnoughWallet.status_code,
        )


@app.route("/gachas-list", methods=["GET"])
@token_required(role_required="Admin")
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


@app.route("/<int:gacha_id>", methods=["GET"])
@token_required(role_required="Admin")
def get_gacha(gacha_id):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    query = """
    SELECT *
    FROM Gacha
    WHERE id = %s;
    """
    cursor.execute(query, (gacha_id,))
    gacha = cursor.fetchall()
    cursor.close()
    connection.close()

    return jsonify(gacha), 200


@app.route("/update/<int:gacha_id>", methods=["PATCH"])
@token_required(role_required="Admin")
def patch_gacha(gacha_id):

    data = request.get_json()

    if (
        not data.get("name")
        and not data.get("rarity")
        and not data.get("description")
        and not data.get("name_img")
    ):
        return jsonify({"message": "No data provided for update."}), 400

    name = data.get("name")
    rarity = data.get("rarity")
    description = data.get("description")
    name_img = data.get("name_img")

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
    if name_img:
        query += "name_img = %s, "
        params.append(name_img)

    query = query.rstrip(", ")

    query += " WHERE id = %s"
    params.append(gacha_id)

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(query, tuple(params))
    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({"message": "Gacha modified successfully."}), 200


@app.route("/add", methods=["POST"])
@token_required(role_required="Admin")
def add_gacha():
    data = request.get_json()
    if not data:
        return jsonify({"message": "Invalid request. JSON data is required."}), 400

    name = data.get("name")
    description = data.get("description")
    name_img = data.get("name_img")
    rarity = data.get("rarity")

    if not name or not rarity:
        return jsonify({"message": "Name and rarity are required fields."}), 400

    if rarity not in ["Common", "Uncommon", "Rare", "Super Rare", "Legendary"]:
        return (
            jsonify(
                {
                    "message": f"Invalid rarity: {rarity}. Must be one of Common, Uncommon, Rare, Super Rare, Legendary."
                }
            ),
            400,
        )

    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        query = """
        INSERT INTO Gacha (name, description, name_img, rarity)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (name, description, name_img, rarity))
        connection.commit()
        new_gacha_id = cursor.lastrowid
    except Exception as e:
        connection.rollback()
        return jsonify({"message": f"Error adding gacha: {str(e)}"}), 500
    finally:
        cursor.close()
        connection.close()

    return (
        jsonify({"message": "Gacha added successfully.", "gacha_id": new_gacha_id}),
        201,
    )


@app.route("/delete/<int:gacha_id>", methods=["DELETE"])
@token_required(role_required="Admin")
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
        user_ids = [{"user_id": user["user_id"], "amount": 500} for user in users]

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
        return jsonify({"message": f"Error deleting gacha: {str(e)}"}), 500
    finally:
        cursor.close()
        connection.close()
        if len(user_ids) > 0:
            refundUsers = requests.post(
                CURRENCY_URL + "/refund",
                json={"users": user_ids},
                headers={
                    "Authorization": "Bearer "
                    + request.headers.get("Authorization", ""),
                    "Content-Type": "application/json",
                },
                cert=(CERT_FILE, KEY_FILE),
                verify=False,
            )
            if refundUsers.status_code == 200:
                return (
                    jsonify(
                        {"message": "Gacha deleted successfully and users refunded!"}
                    ),
                    200,
                )
            else:
                return (
                    jsonify(refundUsers.json()),
                    refundUsers.status_code,
                )
        else:
            return (
                jsonify({"message": "Gacha deleted successfully!"}),
                200,
            )


@app.route("/collection/add", methods=["POST"])
@token_required(role_required="Admin")
def add_gacha_to_user():

    data = request.get_json()
    if not data:
        return jsonify({"message": "Invalid request. JSON data is required."}), 400

    buyer_id = data.get("user_id")
    gacha_id = data.get("gacha_id")

    if not buyer_id or not gacha_id:
        return jsonify({"message": "is missing userId or gachaID."}), 400

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        query_exists = """
        SELECT EXISTS (
            SELECT 1
            FROM Collection
            WHERE user_id = %s AND gacha_id = %s
        ) AS owns;
        """
        cursor.execute(query_exists, (buyer_id, gacha_id))
        owns_dict = cursor.fetchone()
        already_owned = int(owns_dict["owns"])

        if already_owned == 0:
            query_add = """
            INSERT INTO Collection (user_id, gacha_id, quantity)
            VALUES (%s, %s, 1);
            """
            cursor.execute(query_add, (buyer_id, gacha_id))
        else:
            query_update = """
            UPDATE Collection
            SET quantity = quantity + 1
            WHERE user_id = %s AND gacha_id = %s;
            """
            cursor.execute(query_update, (buyer_id, gacha_id))

        connection.commit()
    except Exception as e:
        connection.rollback()
        return jsonify({"message": f"Error adding Gacha: {str(e)}"}), 500
    finally:
        cursor.close()
        connection.close()

    return (
        jsonify(
            {"message": f"Gacha {gacha_id} successfully added to user {buyer_id}."}
        ),
        200,
    )


@app.route("/remove", methods=["POST"])
@token_required(role_required="Admin")
def remove_gacha():
    data = request.get_json()
    if not data or "user_id" not in data or "gacha_id" not in data:
        return jsonify({"message": "user_id and gacha_id are required."}), 400

    user_id = data["user_id"]
    gacha_id = data["gacha_id"]

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    query = """
    SELECT quantity
    FROM Collection
    WHERE user_id = %s AND gacha_id = %s;
    """
    cursor.execute(query, (user_id, gacha_id))
    result = cursor.fetchone()

    if not result:
        cursor.close()
        connection.close()
        return jsonify({"message": "User does not own this gacha."}), 404

    quantity = result["quantity"]

    if quantity <= 1:
        delete_query = """
        DELETE FROM Collection
        WHERE user_id = %s AND gacha_id = %s;
        """
        cursor.execute(delete_query, (user_id, gacha_id))
    else:
        update_query = """
        UPDATE Collection
        SET quantity = quantity - 1
        WHERE user_id = %s AND gacha_id = %s;
        """
        cursor.execute(update_query, (user_id, gacha_id))

    connection.commit()
    cursor.close()
    connection.close()

    return (
        jsonify({"message": f"Gacha with ID {gacha_id} removed from user {user_id}."}),
        200,
    )


if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5001,
        ssl_context=("/run/secrets/https_gacha_cert", "/run/secrets/https_gacha_key"),
    )
