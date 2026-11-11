"""Conexión a MySQL compartida por toda la aplicación."""
import MySQLdb
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash

mysql = MySQL()

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


def asegurar_admin():
    """Crea el usuario administrador por defecto si la tabla usuarios está vacía.

    Se hace desde Python (y no en el script SQL) porque la contraseña
    se guarda con el hash de werkzeug.
    """
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT COUNT(*) AS total FROM usuarios")
        if cur.fetchone()["total"] == 0:
            cur.execute(
                "INSERT INTO usuarios (username, password_hash, nombre, rol) "
                "VALUES (%s, %s, %s, %s)",
                (ADMIN_USERNAME, generate_password_hash(ADMIN_PASSWORD), "Administrador", "ADMIN"),
            )
            mysql.connection.commit()
            print(f"[CAE] Usuario por defecto creado -> {ADMIN_USERNAME} / {ADMIN_PASSWORD}")
        cur.close()
    except MySQLdb.Error as e:
        print(f"[CAE] ⚠ No se pudo conectar a MySQL: {e}")
        print("[CAE]   Revisa config.py y que hayas ejecutado database/cae_db.sql")
