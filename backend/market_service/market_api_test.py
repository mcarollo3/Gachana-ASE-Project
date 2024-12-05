import market_api as main_market_api

flask_app = main_market_api.app

def mock_add_currency():
        return (jsonify({"message": f"{amount} added to user {user_id} wallet successfully!"}), 200)

def mock_check_and_deduct():
    return jsonify({
        "message": "Funds deducted successfully!",
        "new_balance": str(new_balance)
        }, 200)

def mock_collection():
    return jsonify({"message": "User owns no gachas."}), 200

def mock_collection_add():
    return (jsonify({"message": f"Gacha 3 successfully added to user 2."}), 200)

def mock_login():
    return jsonify({"token": "token1234"}, 200)
    
def mock_refund():
    return (jsonify({"message": "Gacha deleted successfully!"}), 200)

def mock_remove():
        return (jsonify({"message": f"Gacha with ID 4 removed from user 1."}), 200)

main_market_api.mock_add_currency = mock_add_currency
main_market_api.mock_check_and_deduct = mock_check_and_deduct
main_market_api.mock_collection = mock_collection
main_market_api.mock_collection_add = mock_collection_add
main_market_api.mock_login = mock_login
main_market_api.mock_refund = mock_refund
main_market_api.mock_remove = mock_remove