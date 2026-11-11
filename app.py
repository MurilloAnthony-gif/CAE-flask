from flask import Flask

from config import Config
from db import asegurar_admin, mysql


def crear_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    mysql.init_app(app)

    # Rutas (blueprints): un archivo por módulo dentro de routes/
    from routes.asistencias import asistencias_bp
    from routes.auth import auth_bp
    from routes.cargos import cargos_bp
    from routes.departamentos import departamentos_bp
    from routes.empleados import empleados_bp
    from routes.horarios import horarios_bp
    from routes.main import main_bp
    from routes.marcador import marcador_bp
    from routes.reportes import reportes_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(departamentos_bp)
    app.register_blueprint(cargos_bp)
    app.register_blueprint(horarios_bp)
    app.register_blueprint(empleados_bp)
    app.register_blueprint(marcador_bp)
    app.register_blueprint(asistencias_bp)
    app.register_blueprint(reportes_bp)

    with app.app_context():
        asegurar_admin()

    return app


app = crear_app()

if __name__ == "__main__":
    app.run(debug=True, port=3000)
