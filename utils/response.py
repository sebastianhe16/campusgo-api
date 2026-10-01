from flask import jsonify

def success_response(data, message, http_code=200):
    return jsonify({
        "data": data,
        "message": message,
        "status": True
    }), http_code

def error_response(message, http_code=400, data=None):
    return jsonify({
        "data": data,
        "message": message,
        "status": False
    }), http_code
