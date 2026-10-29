class ReservaRepository:
    def __init__(self, connection):
        self.connection = connection

    def obtener_pasajero_id_por_usuario(self, usuario_id):
        cursor = self.connection.cursor()
        try:
            # 1. Busca si ya existe en la tabla pasajero
            sql = "SELECT id FROM pasajero WHERE usuario_id = %s"
            cursor.execute(sql, (usuario_id,))
            fila = cursor.fetchone()
            if fila:
                return fila["id"]

            # 2. Si no existe, lo inserta automáticamente y guarda el cambio
            sql_insert = "INSERT INTO pasajero (usuario_id) VALUES (%s)"
            cursor.execute(sql_insert, (usuario_id,))
            self.connection.commit()
            return cursor.lastrowid
        finally:
            cursor.close()

    def obtener_viaje_para_actualizar(self, viaje_id):
        cursor = self.connection.cursor()
        try:
            sql = """
            SELECT
                v.id, v.fecha, v.hora, v.cupos, v.estado,
                c.usuario_id AS conductor_usuario_id
            FROM viaje v
            INNER JOIN conductor c ON c.id = v.conductor_id
            WHERE v.id = %s
            FOR UPDATE
            """
            cursor.execute(sql, (viaje_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
            
            
    def crear_reserva(self, pasajero_id):
        cursor = self.connection.cursor()
        try:
            sql = """
            INSERT INTO reserva (pasajero_id, estado)
            VALUES (%s, 'CONFIRMADA')
            """
            cursor.execute(sql, (pasajero_id,))
            return cursor.lastrowid
        finally:
            cursor.close()

    def crear_detalle(self, reserva_id, viaje_id, cantidad, tipo_tramo, orden):
        cursor = self.connection.cursor()
        try:
            sql = """
            INSERT INTO reserva_viaje (
                reserva_id, viaje_id, cantidad,
                tipo_tramo, orden_tramo, estado
            )
            VALUES (%s, %s, %s, %s, %s, 'CONFIRMADA')
            """
            cursor.execute(
                sql,
                (
                    reserva_id,
                    viaje_id,
                    cantidad,
                    tipo_tramo,
                    orden,
                ),
            )
        finally:
            cursor.close()

    def descontar_cupos(self, viaje_id, cantidad):
        cursor = self.connection.cursor()
        try:
            sql = """
            UPDATE viaje
            SET estado = CASE
                    WHEN cupos - %s <= 0 THEN 'COMPLETO'
                    ELSE estado
                END,
                cupos = cupos - %s
            WHERE id = %s
            """
            cursor.execute(
                sql,
                (
                    cantidad,
                    cantidad,
                    viaje_id,
                ),
            )
        finally:
            cursor.close()
            
    def obtener_reserva_para_actualizar(self, reserva_id):
        cursor = self.connection.cursor()
        try:
            sql = "SELECT id, pasajero_id, estado FROM reserva WHERE id = %s FOR UPDATE"
            cursor.execute(sql, (reserva_id,))
            return cursor.fetchone()
        finally:
            cursor.close()

    def obtener_detalles_reserva(self, reserva_id):
        cursor = self.connection.cursor()
        try:
            sql = "SELECT viaje_id, cantidad, estado FROM reserva_viaje WHERE reserva_id = %s FOR UPDATE"
            cursor.execute(sql, (reserva_id,))
            return cursor.fetchall()
        finally:
            cursor.close()

    def cancelar_reserva(self, reserva_id):
        cursor = self.connection.cursor()
        try:
            sql = "UPDATE reserva SET estado = 'CANCELADA' WHERE id = %s"
            cursor.execute(sql, (reserva_id,))
            return cursor.rowcount
        finally:
            cursor.close()

    def cancelar_detalles(self, reserva_id):
        cursor = self.connection.cursor()
        try:
            sql = "UPDATE reserva_viaje SET estado = 'CANCELADA' WHERE reserva_id = %s"
            cursor.execute(sql, (reserva_id,))
            return cursor.rowcount
        finally:
            cursor.close()

    def devolver_cupos(self, viaje_id, cantidad):
        cursor = self.connection.cursor()
        try:
            sql = """
            UPDATE viaje
            SET cupos = cupos + %s,
                estado = CASE
                    WHEN estado = 'COMPLETO' THEN 'DISPONIBLE'
                    ELSE estado
                END
            WHERE id = %s
            """
            cursor.execute(sql, (cantidad, viaje_id))
            return cursor.rowcount
        finally:
            cursor.close()