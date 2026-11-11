import os


class Config:
    """Configuración de la aplicación.

    Los valores se pueden sobrescribir con variables de entorno
    (por ejemplo MYSQL_PASSWORD) para no subir contraseñas al repositorio.
    """

    SECRET_KEY = os.environ.get("SECRET_KEY", "cae-clave-secreta-cambiar")

    # --- Conexión a MySQL ---
    MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.environ.get("MYSQL_PORT", 3306))
    MYSQL_USER = os.environ.get("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "1234")  
    MYSQL_DB = os.environ.get("MYSQL_DB", "cae_db")
    MYSQL_CHARSET = "utf8mb4"
    MYSQL_CURSORCLASS = "DictCursor"
