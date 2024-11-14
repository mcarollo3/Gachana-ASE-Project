import jwt
from flask import jsonify, request
import os


SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("No SECRET_KEY set for Flask application")


def decode_token(token):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def token_required(role_required):
    def decorator(f):
        def wrapped_function(*args, **kwargs):
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            if not token:
                return jsonify({'message': 'Token is missing!'}), 403

            user_data = decode_token(token)
            if user_data is None or user_data['role'] != role_required:
                return jsonify({'message': 'Unauthorized access!'}), 403

            return f(*args, **kwargs)
        wrapped_function.__name__ = f.__name__
        return wrapped_function
    return decorator