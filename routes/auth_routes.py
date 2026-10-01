from flask import Blueprint, request
from services.auth_service import AuthService
from utils.response import error_response, success_response

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    datos = request.get_json(silent=True)
    if datos is None:
        return error_response("Debe enviar los datos en formato JSON", 400)

    email = str(datos.get("email", "")).strip()
    password = str(datos.get("password", ""))

    if not email or not password:
        return error_response("Email y password son obligatorios", 400)

    service = AuthService()
    data, message, http_code = service.login(email, password)

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)