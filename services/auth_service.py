from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash
from database import get_connection
from repositories.usuario_repository import UsuarioRepository


class AuthService:
    def login(self, email, password):
        connection = get_connection()
        try:
            repository = UsuarioRepository(connection)
            usuario = repository.buscar_por_email(email)

            if usuario is None:
                return None, "Correo o contraseña incorrectos", 401

            if usuario["estado"] != "ACTIVO":
                return None, "El usuario se encuentra inactivo", 403

            if not check_password_hash(usuario["password_hash"], password):
                return None, "Correo o contraseña incorrectos", 401

            token = create_access_token(
                identity=str(usuario["id"]),
                additional_claims={"rol": usuario["rol"]}
            )

            data = {
                "usuario_id": usuario["id"],
                "email": usuario["email"],
                "nombres": usuario["nombres"],
                "apellidos": usuario["apellidos"],
                "rol": usuario["rol"],
                "estado": usuario["estado"],
                "token": token
            }

            return data, "Inicio de sesión satisfactorio", 200

        finally:
            connection.close()