class ViajeRepository:
    def __init__(self, connection):
        self.connection = connection

    def obtener_conductor_id_por_usuario(self, usuario_id):
        cursor = self.connection.cursor()
        try:
            sql = "SELECT id FROM conductor WHERE usuario_id = %s"
            cursor.execute(sql, (usuario_id,))
            fila = cursor.fetchone()
            return fila["id"] if fila else None
        finally:
            cursor.close()

    def crear(self, conductor_id, datos):
        cursor = self.connection.cursor()
        try:
            sql = """
            INSERT INTO viaje (conductor_id, origen, destino, fecha, hora, cupos, precio, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'DISPONIBLE')
            """
            cursor.execute(
                sql,
                (
                    conductor_id,
                    datos["origen"],
                    datos["destino"],
                    datos["fecha"],
                    datos["hora"],
                    datos["cupos"],
                    datos["precio"],
                ),
            )
            return cursor.lastrowid
        finally:
            cursor.close()
            
            
    def listar(self, origen=None, destino=None, fecha=None, estado=None, 
               precio_min=None, precio_max=None, solo_disponibles=False, desde=None):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT
                v.id, v.origen, v.destino, v.fecha, v.hora,
                v.cupos, v.precio, v.estado,
                CONCAT(u.nombres, ' ', u.apellidos) AS conductor
                FROM viaje v
                INNER JOIN conductor c ON c.id = v.conductor_id
                INNER JOIN usuario u ON u.id = c.usuario_id
                WHERE 1 = 1
                """
            params = []
            if origen:
                sql += " AND v.origen LIKE %s"
                params.append(f"%{origen}%")
            if destino:
                sql += " AND v.destino LIKE %s"
                params.append(f"%{destino}%")
            if fecha:
                sql += " AND v.fecha = %s"
                params.append(fecha)
            if estado:
                sql += " AND v.estado = %s"
                params.append(estado)
            # --- NUEVOS FILTROS DE PRECIO ---
            if precio_min is not None:
                sql += " AND v.precio >= %s"
                params.append(precio_min)
            if precio_max is not None:
                sql += " AND v.precio <= %s"
                params.append(precio_max)
                
            if solo_disponibles:
                sql += " AND v.estado = 'DISPONIBLE' AND v.cupos > 0"
            elif estado:
                sql += " AND v.estado = %s"
                params.append(estado)
            
            if desde:
                sql += " AND v.fecha >= %s"
                params.append(desde)

            sql += " ORDER BY v.fecha, v.hora"
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
        finally:
            cursor.close()
    
    def obtener_por_id(self, viaje_id):
        cursor = self.connection.cursor()
        try:
            sql = """
            SELECT
                v.*, c.usuario_id AS conductor_usuario_id
            FROM viaje v
            INNER JOIN conductor c ON c.id = v.conductor_id
            WHERE v.id = %s
            """
            cursor.execute(sql, (viaje_id,))
            return cursor.fetchone()
        finally:
            cursor.close()

    def actualizar(self, viaje_id, datos):
        cursor = self.connection.cursor()
        try:
            sql = """
            UPDATE viaje
            SET origen = %s,
                destino = %s,
                fecha = %s,
                hora = %s,
                cupos = %s,
                precio = %s
            WHERE id = %s
            """
            cursor.execute(
                sql,
                (
                    datos["origen"],
                    datos["destino"],
                    datos["fecha"],
                    datos["hora"],
                    datos["cupos"],
                    datos["precio"],
                    viaje_id,
                ),
            )
            return cursor.rowcount
        finally:
            cursor.close()

    def cancelar(self, viaje_id):
        cursor = self.connection.cursor()
        try:
            sql = """
            UPDATE viaje
            SET estado = 'CANCELADO'
            WHERE id = %s
            """
            cursor.execute(sql, (viaje_id,))
            return cursor.rowcount
        finally:
            cursor.close()

    def listar_por_conductor(self, conductor_id, estado=None):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT id, origen, destino, fecha, hora, cupos, precio, estado
                FROM viaje
                WHERE conductor_id = %s
                """
            params = [conductor_id]
            if estado:
                sql += " AND estado = %s"
                params.append(estado)
            sql += " ORDER BY fecha DESC, hora DESC"
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
        finally:
            cursor.close()
            
    def actualizar_cupos(self, viaje_id, cupos):
        cursor = self.connection.cursor()
        try:
            sql = "UPDATE viaje SET cupos = %s WHERE id = %s"
            cursor.execute(sql, (cupos, viaje_id))
            return cursor.rowcount
        finally:
            cursor.close()
            
    def cambiar_estado(self, viaje_id, nuevo_estado):
        cursor = self.connection.cursor()
        try:
            sql = "UPDATE viaje SET estado = %s WHERE id = %s"
            cursor.execute(sql, (nuevo_estado, viaje_id))
            return cursor.rowcount
        finally:
            cursor.close()
            
    def existe_viaje_duplicado(self, conductor_id, fecha, hora, origen, destino):
        cursor = self.connection.cursor()
        try:
            sql = """
            SELECT id FROM viaje
            WHERE conductor_id = %s
            AND fecha = %s
            AND hora = %s
            AND origen = %s
            AND destino = %s
            AND estado != 'CANCELADO'
            LIMIT 1
            """
            cursor.execute(sql, (conductor_id, fecha, hora, origen, destino))
            return cursor.fetchone() is not None
        finally:
            cursor.close()
            
    