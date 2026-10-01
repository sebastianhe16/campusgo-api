from datetime import datetime

from database import get_connection
from repositories.reserva_repository import ReservaRepository
from datetime import timedelta

class ReservaService:
    
    def crear(self, usuario_id, datos):
        viajes = datos.get("viajes", [])

        if not isinstance(viajes, list) or len(viajes) not in (1, 2):
            return None, "Debe seleccionar uno o dos viajes", 400

        ids = [v.get("viaje_id") for v in viajes]

        if None in ids or len(ids) != len(set(ids)):
            return None, "Los viajes son inválidos o están repetidos", 400

        connection = get_connection()

        try:
            connection.begin()
            repository = ReservaRepository(connection)

            pasajero_id = repository.obtener_pasajero_id_por_usuario(usuario_id)

            if pasajero_id is None:
                connection.rollback()
                return None, "El usuario no posee perfil de pasajero", 403
            viajes_bd = []

            for item in viajes:
                cantidad = int(item.get("cantidad", 0))
                tipo = item.get("tipo_tramo")

                if cantidad <= 0 or tipo not in ("IDA", "RETORNO"):
                    connection.rollback()
                    return None, "Datos de tramo inválidos", 400

                viaje = repository.obtener_viaje_para_actualizar(
                    item["viaje_id"]
                )

                if viaje is None:
                    connection.rollback()
                    return None, "Uno de los viajes no existe", 404

                if viaje["estado"] != "DISPONIBLE":
                    connection.rollback()
                    return None, "Uno de los viajes no está disponible", 409

                if viaje["cupos"] < cantidad:
                    connection.rollback()
                    return None, "No existen cupos suficientes", 409

                if str(viaje["conductor_usuario_id"]) == str(usuario_id):
                    connection.rollback()
                    return None, "No puede reservar su propio viaje", 409

                viajes_bd.append((item, viaje))
                
                if len(viajes_bd) == 2:
                    tipos = {item["tipo_tramo"] for item, _ in viajes_bd}

                    if tipos != {"IDA", "RETORNO"}:
                        connection.rollback()
                        return None, "Debe seleccionar IDA y RETORNO", 400

                    ida = next(
                        (item, v) for item, v in viajes_bd
                        if item["tipo_tramo"] == "IDA"
                    )

                    retorno = next(
                        (item, v) for item, v in viajes_bd
                        if item["tipo_tramo"] == "RETORNO"
                    )

                    hora_ida = ida[1]["hora"]
                    if isinstance(hora_ida, timedelta):
                        hora_ida = (datetime.min + hora_ida).time()

                    fecha_ida = datetime.combine(
                        ida[1]["fecha"],
                        hora_ida
                    )

                    hora_retorno = retorno[1]["hora"]
                    if isinstance(hora_retorno, timedelta):
                        hora_retorno = (datetime.min + hora_retorno).time()

                    fecha_retorno = datetime.combine(
                        retorno[1]["fecha"],
                        hora_retorno
                    )

                    if fecha_retorno <= fecha_ida:
                        connection.rollback()
                        return None, "El retorno debe ser posterior a la ida", 409

            reserva_id = repository.crear_reserva(pasajero_id)

            orden = 1

            for item, viaje in viajes_bd:
                repository.crear_detalle(
                    reserva_id,
                    item["viaje_id"],
                    int(item["cantidad"]),
                    item["tipo_tramo"],
                    orden
                )

                repository.descontar_cupos(
                    item["viaje_id"],
                    int(item["cantidad"])
                )

                orden += 1

            connection.commit()

            return {
                "reserva_id": reserva_id
            }, "Reserva registrada correctamente", 201

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    def cancelar(self, usuario_id, reserva_id):
        connection = get_connection()
        try:
            connection.begin()
            repository = ReservaRepository(connection)

            # 1. Validar que el usuario sea un pasajero registrado
            pasajero_id = repository.obtener_pasajero_id_por_usuario(usuario_id)
            if pasajero_id is None:
                connection.rollback()
                return None, "El usuario no posee perfil de pasajero", 403

            # 2. Bloquear y verificar existencia de la reserva
            reserva = repository.obtener_reserva_para_actualizar(reserva_id)
            if reserva is None:
                connection.rollback()
                return None, "Reserva no encontrada", 404

            # 3. Validar propiedad (solo el pasajero dueño puede cancelar)
            if reserva["pasajero_id"] != pasajero_id:
                connection.rollback()
                return None, "No puede cancelar una reserva que no le pertenece", 403

            # 4. Validar estado actual
            if reserva["estado"] == "CANCELADA":
                connection.rollback()
                return None, "La reserva ya se encuentra cancelada", 409

            # 5. Obtener los tramos (IDA y/o RETORNO) bloqueando sus registros
            detalles = repository.obtener_detalles_reserva(reserva_id)
            if not detalles:
                connection.rollback()
                return None, "La reserva no contiene tramos asociados", 404

            # 6. Ejecutar cancelaciones lógicas
            repository.cancelar_reserva(reserva_id)
            repository.cancelar_detalles(reserva_id)

            # 7. Restituir cupos en la tabla viaje para cada tramo
            for detalle in detalles:
                if detalle["estado"] != "CANCELADA":
                    repository.devolver_cupos(detalle["viaje_id"], detalle["cantidad"])

            # 8. Confirmar todos los cambios atómicamente
            connection.commit()
            return {
                "reserva_id": reserva_id,
                "estado": "CANCELADA"
            }, "Reserva cancelada correctamente y cupos devueltos", 200

        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()