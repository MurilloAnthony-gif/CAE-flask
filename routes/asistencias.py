from datetime import timedelta
import MySQLdb
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from db import mysql
from routes.auth import login_required
from routes.marcador import calcular_atraso

asistencias_bp = Blueprint("asistencias", __name__, url_prefix="/asistencias")


def _formatear_hora(val):
    if val is None:
        return ""
    if isinstance(val, timedelta):
        tot = int(val.total_seconds())
        h = tot // 3600
        m = (tot % 3600) // 60
        return f"{h:02d}:{m:02d}"
    if hasattr(val, "strftime"):
        return val.strftime("%H:%M")
    partes = str(val).split(":")
    if len(partes) >= 2:
        return f"{int(partes[0]):02d}:{int(partes[1]):02d}"
    return str(val)


def _formatear_fecha(val):
    if val is None:
        return ""
    if hasattr(val, "strftime"):
        return val.strftime("%Y-%m-%d")
    return str(val)


@asistencias_bp.route("/")
@login_required
def index():
    cur = mysql.connection.cursor()
    cur.execute(
        """
        SELECT a.*,
               CONCAT(e.nombres, ' ', e.apellidos) AS empleado,
               u.nombre AS registrado_por_nombre
        FROM asistencias a
        INNER JOIN empleados e ON e.id = a.empleado_id
        LEFT JOIN usuarios u ON u.id = a.registrado_por
        ORDER BY a.fecha DESC, a.hora_entrada DESC
        LIMIT 100
        """
    )
    asistencias = cur.fetchall()
    cur.close()

    for a in asistencias:
        a["hora_entrada"] = _formatear_hora(a["hora_entrada"])
        a["hora_salida"] = _formatear_hora(a["hora_salida"])
        a["fecha"] = _formatear_fecha(a["fecha"])

    return render_template("asistencias/index.html", asistencias=asistencias)


@asistencias_bp.route("/ajustar", methods=["GET", "POST"])
@asistencias_bp.route("/ajustar/<int:id>", methods=["GET", "POST"])
@login_required
def ajustar(id=None):
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT id, cedula, nombres, apellidos FROM empleados WHERE activo = 1 ORDER BY apellidos, nombres"
    )
    empleados = cur.fetchall()

    asistencia = None
    if id is not None:
        cur.execute("SELECT * FROM asistencias WHERE id = %s", (id,))
        asistencia = cur.fetchone()
        if not asistencia:
            cur.close()
            flash("Registro de asistencia no encontrado", "warning")
            return redirect(url_for("asistencias.index"))

    if request.method == "POST":
        observacion = request.form.get("observacion", "").strip()
        hora_entrada = request.form.get("hora_entrada", "").strip() or None
        hora_salida = request.form.get("hora_salida", "").strip() or None

        if not observacion:
            flash("El motivo del ajuste es obligatorio", "danger")
            cur.close()
            if asistencia:
                asistencia["fecha"] = _formatear_fecha(asistencia["fecha"])
                asistencia["hora_entrada"] = _formatear_hora(asistencia["hora_entrada"])
                asistencia["hora_salida"] = _formatear_hora(asistencia["hora_salida"])
            return render_template("asistencias/form.html", asistencia=asistencia, empleados=empleados)

        admin_id = session.get("user_id") or session.get("usuario_id")

        if asistencia:
            empleado_id = asistencia["empleado_id"]
            fecha = asistencia["fecha"]
        else:
            empleado_id = request.form.get("empleado_id")
            fecha = request.form.get("fecha", "").strip()

            if not empleado_id or not fecha:
                flash("Debes seleccionar el empleado y la fecha", "danger")
                cur.close()
                return render_template("asistencias/form.html", asistencia=None, empleados=empleados)

        # Consultar horario del empleado para calcular atraso si hay hora_entrada
        cur.execute(
            """
            SELECT h.hora_entrada, h.tolerancia_min
            FROM empleados e
            INNER JOIN horarios h ON h.id = e.horario_id
            WHERE e.id = %s
            """,
            (empleado_id,),
        )
        horario = cur.fetchone()

        minutos_atraso = 0
        estado = "PUNTUAL"
        if hora_entrada and horario:
            minutos_atraso, estado = calcular_atraso(
                hora_entrada, horario["hora_entrada"], horario["tolerancia_min"]
            )

        try:
            if asistencia:
                cur.execute(
                    """
                    UPDATE asistencias
                    SET hora_entrada = %s, hora_salida = %s, minutos_atraso = %s,
                        estado = %s, metodo = 'AJUSTE', observacion = %s, registrado_por = %s
                    WHERE id = %s
                    """,
                    (
                        hora_entrada,
                        hora_salida,
                        minutos_atraso,
                        estado,
                        observacion,
                        admin_id,
                        asistencia["id"],
                    ),
                )
                flash("Asistencia ajustada correctamente", "success")
            else:
                cur.execute(
                    "SELECT id FROM asistencias WHERE empleado_id = %s AND fecha = %s",
                    (empleado_id, fecha),
                )
                existente = cur.fetchone()
                if existente:
                    cur.execute(
                        """
                        UPDATE asistencias
                        SET hora_entrada = %s, hora_salida = %s, minutos_atraso = %s,
                            estado = %s, metodo = 'AJUSTE', observacion = %s, registrado_por = %s
                        WHERE id = %s
                        """,
                        (
                            hora_entrada,
                            hora_salida,
                            minutos_atraso,
                            estado,
                            observacion,
                            admin_id,
                            existente["id"],
                        ),
                    )
                    flash("Asistencia actualizada mediante ajuste", "success")
                else:
                    cur.execute(
                        """
                        INSERT INTO asistencias
                            (empleado_id, fecha, hora_entrada, hora_salida, minutos_atraso,
                             estado, metodo, observacion, registrado_por)
                        VALUES (%s, %s, %s, %s, %s, %s, 'AJUSTE', %s, %s)
                        """,
                        (
                            empleado_id,
                            fecha,
                            hora_entrada,
                            hora_salida,
                            minutos_atraso,
                            estado,
                            observacion,
                            admin_id,
                        ),
                    )
                    flash("Ajuste registrado correctamente", "success")

            mysql.connection.commit()
            cur.close()
            return redirect(url_for("asistencias.index"))
        except MySQLdb.Error as e:
            flash(f"Error al guardar el ajuste: {e}", "danger")

    cur.close()
    if asistencia:
        asistencia["fecha"] = _formatear_fecha(asistencia["fecha"])
        asistencia["hora_entrada"] = _formatear_hora(asistencia["hora_entrada"])
        asistencia["hora_salida"] = _formatear_hora(asistencia["hora_salida"])

    return render_template("asistencias/form.html", asistencia=asistencia, empleados=empleados)


@asistencias_bp.route("/eliminar/<int:id>", methods=["POST"])
@login_required
def eliminar(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM asistencias WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    flash("Registro de asistencia eliminado", "info")
    return redirect(url_for("asistencias.index"))
