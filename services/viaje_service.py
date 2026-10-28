from database import get_connection
from repositories.viaje_repository import ViajeRepository
import cloudinary
import cloudinary.uploader
from datetime import timedelta
from datetime import datetime, date, timedelta


ALLOWED_IMAGE_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}
MAX_IMAGE_SIZE = 5 * 1024 * 1024

class ViajeService:
    def subir_foto_vehiculo(self, usuario_id, archivo):
        if archivo is None or not archivo.filename:
            return None, "Debe seleccionar una imagen", 400

        if archivo.mimetype not in ALLOWED_IMAGE_TYPES:
            return None, "La imagen debe ser JPG, PNG o WEBP", 400

        contenido = archivo.stream.read(MAX_IMAGE_SIZE + 1)
        archivo.stream.seek(0)
        if len(contenido) > MAX_IMAGE_SIZE:
            return None, "La imagen no puede superar los 5 MB", 400

        try:
            resultado = cloudinary.uploader.upload(
                archivo,
                folder="campusgo/vehiculos",
                resource_type="image",
                format=ALLOWED_IMAGE_TYPES[archivo.mimetype],
            )
            url = resultado.get("secure_url")
            if not url:
                return None, "Cloudinary no devolvió la URL de la imagen", 502

            connection = get_connection()
            try:
                repository = ViajeRepository(connection)
                if repository.guardar_foto_vehiculo(usuario_id, url) == 0:
                    return None, "El usuario no posee perfil de conductor", 404
                connection.commit()
                return {"foto_vehiculo_url": url}, "Foto del vehículo actualizada correctamente", 200
            except Exception:
                connection.rollback()
                raise
            finally:
                connection.close()
        except Exception as error:
            if isinstance(error, (KeyError, ValueError)):
                return None, "No se pudo procesar la imagen", 400
            raise

    def obtener_foto_vehiculo(self, usuario_id):
        connection = get_connection()
        try:
            repository = ViajeRepository(connection)
            foto = repository.obtener_foto_vehiculo_por_usuario(usuario_id)
            if foto is None:
                return None, "No se encontró una foto de vehículo para este conductor", 404
            return {"foto_vehiculo_url": foto}, "Foto del vehículo obtenida correctamente", 200
        finally:
            connection.close()

    def crear(self, usuario_id, datos):
        obligatorios = ["origen", "destino", "fecha", "hora", "cupos", "precio"]
        if any(campo not in datos for campo in obligatorios):
            return None, "Faltan datos obligatorios", 400

        if int(datos["cupos"]) <= 0:
            return None, "Los cupos deben ser mayores que cero", 400

        if float(datos["precio"]) < 0:
            return None, "El precio no puede ser negativo", 400

        connection = get_connection()
        try:
            repository = ViajeRepository(connection)
            conductor_id = repository.obtener_conductor_id_por_usuario(usuario_id)
            
            if conductor_id is None:
                return None, "El usuario no posee perfil de conductor", 403
            
            if repository.existe_viaje_duplicado(conductor_id, datos["fecha"], datos["hora"], datos["origen"], datos["destino"]):
                return None, "Ya tiene un viaje programado con el mismo itinerario en la misma fecha y hora", 409
                    
            viaje_id = repository.crear(conductor_id, datos)
            connection.commit()
            return {"viaje_id": viaje_id}, "Viaje creado correctamente", 201
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def listar(self, filtros):
        p_min = filtros.get("precio_min")
        p_max = filtros.get("precio_max")

        precio_min_val = None
        precio_max_val = None
        
        try:
            if p_min is not None and str(p_min).strip() != "":
                precio_min_val = float(p_min)
                if precio_min_val < 0:
                    return None, "El precio mínimo no puede ser negativo", 400
            if p_max is not None and str(p_max).strip() != "":
                precio_max_val = float(p_max)
                if precio_max_val < 0:
                    return None, "El precio máximo no puede ser negativo", 400
        except ValueError:
            return None, "Los valores de precio deben ser numéricos", 400

        if precio_min_val is not None and precio_max_val is not None:
            if precio_min_val > precio_max_val:
                return None, "El precio mínimo no puede ser mayor que el precio máximo", 400
        
        
        connection = get_connection()
        solo_disp = str(filtros.get("solo_disponibles", "")).lower() in ("true", "1", "si")
        
        desde_str = filtros.get("desde")
        desde_val = None
        if desde_str:
            try:
                desde_val = datetime.strptime(desde_str.strip(), "%Y-%m-%d").date()
            except ValueError:
                return None, "El formato de fecha 'desde' debe ser YYYY-MM-DD", 400
            
        try:
            repository = ViajeRepository(connection)
            viajes = repository.listar(
                filtros.get("origen"),
                filtros.get("destino"),
                filtros.get("fecha"),
                filtros.get("estado"),
                precio_min_val,
                precio_max_val,
                solo_disponibles=solo_disp
            )
            for viaje in viajes:
                if isinstance(viaje.get("hora"), timedelta):
                    viaje["hora"] = str(viaje["hora"])
                if isinstance(viaje.get("fecha"), date):
                    viaje["fecha"] = viaje["fecha"].isoformat()
            return viajes, "Viajes obtenidos correctamente", 200
        finally:
            connection.close()

    def obtener(self, viaje_id):
        connection = get_connection()
        try:
            repository = ViajeRepository(connection)
            viaje = repository.obtener_por_id(viaje_id)
            if viaje is None:
                return None, "Viaje no encontrado", 404

            if isinstance(viaje.get("hora"), timedelta):
                viaje["hora"] = str(viaje["hora"])

            if isinstance(viaje.get("fecha"), date):
                viaje["fecha"] = viaje["fecha"].isoformat()

            return viaje, "Viaje obtenido correctamente", 200
        finally:
            connection.close()

    def actualizar(self, usuario_id, viaje_id, datos):
        connection = get_connection()
        try:
            repository = ViajeRepository(connection)
            viaje = repository.obtener_por_id(viaje_id)

            if viaje is None:
                return None, "Viaje no encontrado", 404

            if str(viaje["conductor_usuario_id"]) != str(usuario_id):
                return None, "No puede modificar un viaje de otro conductor", 403

            if viaje["estado"] in ("FINALIZADO", "CANCELADO"):
                return None, "El estado actual no permite modificar el viaje", 409

            repository.actualizar(viaje_id, datos)
            connection.commit()
            return {"viaje_id": viaje_id}, "Viaje actualizado correctamente", 200
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def cancelar(self, usuario_id, viaje_id):
        connection = get_connection()
        try:
            repository = ViajeRepository(connection)
            viaje = repository.obtener_por_id(viaje_id)

            if viaje is None:
                return None, "Viaje no encontrado", 404

            if str(viaje["conductor_usuario_id"]) != str(usuario_id):
                return None, "No puede cancelar un viaje de otro conductor", 403

            if viaje["estado"] == "CANCELADO":
                return None, "El viaje ya se encuentra cancelado", 409

            repository.cancelar(viaje_id)
            connection.commit()
            return {"viaje_id": viaje_id}, "Viaje cancelado correctamente", 200
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
            
    
    def listar_mis_viajes(self, usuario_id, estado=None):
        connection = get_connection()
        try:
            repository = ViajeRepository(connection)
            conductor_id = repository.obtener_conductor_id_por_usuario(usuario_id)
            if conductor_id is None:
                return None, "El usuario no posee perfil de conductor", 403

            viajes = repository.listar_por_conductor(conductor_id, estado)
            for viaje in viajes:
                if isinstance(viaje.get("hora"), timedelta):
                    viaje["hora"] = str(viaje["hora"])
                if isinstance(viaje.get("fecha"), date):
                    viaje["fecha"] = viaje["fecha"].isoformat()
            return viajes, "Mis viajes obtenidos correctamente", 200
        finally:
            connection.close()
            
    def actualizar_cupos(self, usuario_id, viaje_id, datos):
        if "cupos" not in datos:
            return None, "El campo 'cupos' es obligatorio", 400
        try:
            cupos = int(datos["cupos"])
            if cupos < 0:
                return None, "Los cupos no pueden ser negativos", 400
        except (ValueError, TypeError):
            return None, "El valor de cupos debe ser un entero", 400

        connection = get_connection()
        try:
            repository = ViajeRepository(connection)
            viaje = repository.obtener_por_id(viaje_id)
            if viaje is None:
                return None, "Viaje no encontrado", 404
            if str(viaje["conductor_usuario_id"]) != str(usuario_id):
                return None, "No puede modificar un viaje de otro conductor", 403
            if viaje["estado"] in ("FINALIZADO", "CANCELADO"):
                return None, "No se pueden modificar cupos de un viaje finalizado o cancelado", 409

            repository.actualizar_cupos(viaje_id, cupos)
            connection.commit()
            return {"viaje_id": viaje_id, "cupos": cupos}, "Cupos actualizados correctamente", 200
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
            
    def cambiar_estado(self, usuario_id, viaje_id, datos):
        nuevo_estado = str(datos.get("estado", "")).strip().upper()
        estados_permitidos = ("DISPONIBLE", "COMPLETO", "FINALIZADO", "CANCELADO")

        if nuevo_estado not in estados_permitidos:
            return None, f"Estado no permitido. Debe ser: {', '.join(estados_permitidos)}", 400

        connection = get_connection()
        try:
            repository = ViajeRepository(connection)
            viaje = repository.obtener_por_id(viaje_id)
            if viaje is None:
                return None, "Viaje no encontrado", 404
            if str(viaje["conductor_usuario_id"]) != str(usuario_id):
                return None, "No puede modificar el estado de un viaje ajeno", 403

            estado_actual = viaje["estado"]

            # Control de transiciones incoherentes
            if estado_actual == "CANCELADO":
                return None, "Un viaje cancelado no puede cambiar de estado", 409
            if estado_actual == "FINALIZADO":
                return None, "Un viaje finalizado no puede volver a estar activo", 409
            if estado_actual == nuevo_estado:
                return None, f"El viaje ya se encuentra en estado {nuevo_estado}", 409

            repository.cambiar_estado(viaje_id, nuevo_estado)
            connection.commit()
            return {"viaje_id": viaje_id, "nuevo_estado": nuevo_estado}, "Estado actualizado correctamente", 200
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()