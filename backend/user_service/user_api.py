from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/user')
def user():
    return jsonify({"message": "User Service"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)