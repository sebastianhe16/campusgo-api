from flask import Blueprint
from flask_jwt_extended import get_jwt_identity, jwt_required
from services.usuario_service import UsuarioService
from utils.response import error_response, success_response

usuario_bp = Blueprint("usuarios", __name__)


@usuario_bp.route("/api/perfil", methods=["GET"])
@jwt_required()
def obtener_perfil():
    usuario_id = get_jwt_identity()
    service = UsuarioService()
    data, message, http_code = service.obtener_perfil(usuario_id)

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)