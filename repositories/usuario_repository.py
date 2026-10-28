class UsuarioRepository:
    def __init__(self, connection):
        self.connection = connection

    def buscar_por_email(self, email):
        cursor = self.connection.cursor()
        try:
            sql = """
            SELECT
                id,
                email,
                password_hash,
                nombres,
                apellidos,
                rol,
                estado
            FROM usuario
            WHERE email = %s
            LIMIT 1
            """
            cursor.execute(sql, (email,))
            return cursor.fetchone()
        finally:
            cursor.close()

    def buscar_por_id(self, usuario_id):
        cursor = self.connection.cursor()
        try:
            sql = """
            SELECT
                id,
                email,
                nombres,
                apellidos,
                rol,
                estado,
                fecha_registro
            FROM usuario
            WHERE id = %s
            LIMIT 1
            """
            cursor.execute(sql, (usuario_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
            
    def obtener_foto_por_usuario(self, usuario_id):
        """
        Devuelve únicamente los datos necesarios para autorizar
        y localizar la foto del usuario autenticado.
        """
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT id, foto, estado
                FROM usuario
                WHERE id = %s
                LIMIT 1
            """
            cursor.execute(sql, (usuario_id,))
            return cursor.fetchone()
        finally:
            cursor.close()