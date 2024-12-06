import market_api as main_market_api
from flask import jsonify

flask_app = main_market_api.app

def mock_add_currency():
        return jsonify({"message": f"500 added to user 4 wallet successfully!", "status_code":200})

def mock_check_and_deduct():
    return jsonify({
        "message": "Funds deducted successfully!",
        "new_balance": 10
        }, 200)

def mock_collection():
    return jsonify({"message": "User owns no gachas.", "status_code":200})

def mock_collection_add():
    return jsonify({"message": f"Gacha 3 successfully added to user 2.", "status_code":200})

def mock_login():
    return jsonify({"token": "token1234"}, 200)
    
def mock_refund():
    return (jsonify({"message": "Gacha deleted successfully!"}), 200)

def mock_remove():
        return jsonify({"message": f"Gacha with ID 4 removed from user 1.", "status_code":200})

main_market_api.mock_add_currency = mock_add_currency
main_market_api.mock_check_and_deduct = mock_check_and_deduct
main_market_api.mock_collection = mock_collection
main_market_api.mock_collection_add = mock_collection_add
main_market_api.mock_login = mock_login
main_market_api.mock_refund = mock_refund
main_market_api.mock_remove = mock_remove

if __name__ == "__main__":
    main_market_api.app.run(
        debug=False,
        host="0.0.0.0",
        port=5003,
        ssl_context=("/run/secrets/https_market_cert", "/run/secrets/https_market_key"),
    )
