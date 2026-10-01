from werkzeug.security import generate_password_hash
from database import get_connection

USUARIOS = [
    ("juan.perez@usat.edu.pe", "CampusGo#2026", "Juan", "Pérez Sánchez", "PASAJERO", "ACTIVO"),
    ("carlos.mendoza@usat.edu.pe", "CampusGo#2026", "Carlos", "Mendoza Ruiz", "CONDUCTOR", "ACTIVO"),
    ("admin@campusgo.pe", "CampusGo#2026", "Administrador", "CampusGo", "ADMINISTRADOR", "ACTIVO")
]

def main():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        sql = '''
            INSERT INTO usuario (
                email, password_hash, nombres, apellidos, rol, estado
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                password_hash = VALUES(password_hash),
                nombres = VALUES(nombres),
                apellidos = VALUES(apellidos),
                rol = VALUES(rol),
                estado = VALUES(estado)
        '''

        for email, password, nombres, apellidos, rol, estado in USUARIOS:
            cursor.execute(
                sql,
                (
                    email,
                    generate_password_hash(password),
                    nombres,
                    apellidos,
                    rol,
                    estado
                )
            )

        connection.commit()
        print("Usuarios de prueba creados/actualizados correctamente.")

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    main()
