from flask import Blueprint, request
from flask_jwt_extended import (
 jwt_required,
 get_jwt_identity,
 get_jwt
)
from services.reserva_service import ReservaService
from utils.response import success_response, error_response

reserva_bp = Blueprint("reservas", __name__)


@reserva_bp.route("/api/reservas", methods=["POST"])
@jwt_required()
def crear_reserva():
    claims = get_jwt()
    if claims.get("rol") != "PASAJERO":
        return error_response("Se requiere rol PASAJERO", 403)
    datos = request.get_json(silent=True) or {}
    data, message, code = ReservaService().crear(
        get_jwt_identity(),
        datos
    )

    if data is None:
        return error_response(message, code)
    return success_response(data, message, code)

@reserva_bp.route("/api/reservas/<int:reserva_id>", methods=["DELETE"])
@jwt_required()
def cancelar_reserva(reserva_id):
    claims = get_jwt()
    if claims.get("rol") != "PASAJERO":
        return error_response("Se requiere rol PASAJERO", 403)

    data, message, code = ReservaService().cancelar(get_jwt_identity(), reserva_id)
    if data is None:
        return error_response(message, code)
    return success_response(data, message, code)