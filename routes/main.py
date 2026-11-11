import MySQLdb
from flask import Blueprint, abort, current_app, jsonify, redirect, render_template, url_for

from db import mysql
from routes.auth import login_required

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def raiz():
    return redirect(url_for("dashboard.index"))


@dashboard_bp.route("/dashboard")
@login_required
def index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) AS total FROM empleados WHERE activo = 1")
    total_empleados = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) AS total FROM asistencias WHERE fecha = CURDATE()")
    asistencias_hoy = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) AS total FROM asistencias WHERE fecha = CURDATE() AND estado = 'ATRASO'")
    atrasos_hoy = cur.fetchone()["total"]
    cur.close()

    return render_template(
        "dashboard.html",
        total_empleados=total_empleados,
        asistencias_hoy=asistencias_hoy,
        atrasos_hoy=atrasos_hoy,
    )


dashboard = index
main_bp = dashboard_bp


@dashboard_bp.route("/estado-db")
def estado_db():
    """Prueba rápida de la conexión (solo disponible en modo debug)."""
    if not current_app.debug:
        abort(404)
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT VERSION() AS version, DATABASE() AS base, NOW() AS hora_servidor")
        info = cur.fetchone()
        cur.execute("SHOW TABLES")
        tablas = [list(fila.values())[0] for fila in cur.fetchall()]
        cur.close()
        return jsonify(
            conectado=True,
            version_mysql=info["version"],
            base_de_datos=info["base"],
            hora_servidor=str(info["hora_servidor"]),
            tablas=tablas,
        )
    except MySQLdb.Error as e:
        return jsonify(conectado=False, error=str(e)), 500
