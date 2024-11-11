from flask import Flask, json, request, make_response, jsonify

app = Flask(__name__, instance_relative_config=True)

@app.route('/')
def home():
    return '<h1>Hello!</h1>'  



if __name__ == '__main__':
    app.run(debug=True)