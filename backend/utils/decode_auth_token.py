import jwt
from flask import jsonify, request
import os
from get_secrets import get_secret_value


SECRET_KEY = get_secret_value(os.environ.get('SECRET_KEY'))
if not SECRET_KEY:
    raise ValueError("No SECRET_KEY set for Flask application")


def decode_token(token):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return 'Token expired'  
    except jwt.InvalidTokenError:
        return 'Invalid token' 



def token_required(role_required=None):
    if role_required is None:
        role_required = []  

    if isinstance(role_required, str):
        role_required = [role_required]
    
    def decorator(f):
        def wrapped_function(*args, **kwargs):
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            if not token:
                return jsonify({'message': 'Token is missing!'}), 403

           
            user_data = decode_token(token)
            if user_data == 'Invalid token' or user_data == 'Token expired':
                return jsonify({'message': 'Invalid or expired token!'}), 403

            
            user_role = user_data.get('role')
            if not user_role or user_role not in role_required:
                return jsonify({'message': 'Unauthorized access!'}), 403

            
            return f(*args, **kwargs)
        wrapped_function.__name__ = f.__name__
        return wrapped_function
    return decorator

