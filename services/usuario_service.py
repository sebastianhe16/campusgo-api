from database import get_connection
from repositories.usuario_repository import UsuarioRepository


class UsuarioService:
    def obtener_perfil(self, usuario_id):
        connection = get_connection()
        try:
            repository = UsuarioRepository(connection)
            usuario = repository.buscar_por_id(usuario_id)

            if usuario is None:
                return None, "Usuario no encontrado", 404

            if usuario["estado"] != "ACTIVO":
                return None, "El usuario se encuentra inactivo", 403

            data = {
                "usuario_id": usuario["id"],
                "email": usuario["email"],
                "nombres": usuario["nombres"],
                "apellidos": usuario["apellidos"],
                "rol": usuario["rol"],
                "estado": usuario["estado"],
                "fecha_registro": (
                    usuario["fecha_registro"].isoformat()
                    if usuario["fecha_registro"] is not None
                    else None
                ),
            }

            return data, "Perfil obtenido correctamente", 200

        finally:
            connection.close()