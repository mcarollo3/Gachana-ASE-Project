import gacha_api as main_gacha_api
from flask import jsonify

flask_app = main_gacha_api.app

def mock_check_and_deduct():
    return jsonify({
        "message": "Funds deducted successfully!",
        "new_balance": 10
        }, 200)

def mock_refund():
    return (jsonify({"message": "Gacha deleted successfully!"}), 200)

main_gacha_api.mock_check_and_deduct = mock_check_and_deduct
main_gacha_api.mock_refund = mock_refund

if __name__ == "__main__":
    main_gacha_api.app.run(
        debug=False,
        host="0.0.0.0",
        port=5001,
        ssl_context=("/run/secrets/https_gacha_cert", "/run/secrets/https_gacha_key"),
    )
