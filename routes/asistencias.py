import MySQLdb
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from db import mysql
from routes.auth import login_required
from routes.marcador import calcular_atraso

asistencias_bp = Blueprint("asistencias", __name__, url_prefix="/asistencias")


@asistencias_bp.route("/")
@login_required
def index():
    cur = mysql.connection.cursor()
    cur.execute(
        """
        SELECT a.*,
               e.cedula, e.nombres, e.apellidos,
               d.nombre AS departamento_nombre,
               u.nombre AS admin_nombre
        FROM asistencias a
        INNER JOIN empleados e ON e.id = a.empleado_id
        INNER JOIN departamentos d ON d.id = e.departamento_id
        LEFT JOIN usuarios u ON u.id = a.registrado_por
        ORDER BY a.fecha DESC, a.hora_entrada DESC
        LIMIT 100
        """
    )
    asistencias = cur.fetchall()

    cur.execute(
        "SELECT id, cedula, nombres, apellidos FROM empleados WHERE activo = 1 ORDER BY apellidos, nombres"
    )
    empleados = cur.fetchall()
    cur.close()

    return render_template("asistencias/index.html", asistencias=asistencias, empleados=empleados)


@asistencias_bp.route("/ajuste", methods=["POST"])
@login_required
def crear_ajuste():
    """Permite al administrador registrar o corregir una asistencia manualmente.

    Por auditoría, exige una observación (motivo), marca metodo='AJUSTE' y
    guarda en registrado_por el id del administrador en sesión.
    """
    empleado_id = request.form.get("empleado_id")
    fecha = request.form.get("fecha", "").strip()
    hora_entrada = request.form.get("hora_entrada", "").strip()
    hora_salida = request.form.get("hora_salida", "").strip() or None
    observacion = request.form.get("observacion", "").strip()

    if not all([empleado_id, fecha, hora_entrada, observacion]):
        flash(
            "Para un ajuste administrativo son obligatorios: empleado, fecha, hora de entrada y el motivo/observación",
            "danger",
        )
        return redirect(url_for("asistencias.index"))

    cur = mysql.connection.cursor()
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
    if not horario:
        cur.close()
        flash("Empleado no encontrado", "danger")
        return redirect(url_for("asistencias.index"))

    minutos_atraso, estado = calcular_atraso(
        hora_entrada, horario["hora_entrada"], horario["tolerancia_min"]
    )
    admin_id = session.get("usuario_id")

    # Si ya existe asistencia ese día, la actualiza como AJUSTE; si no, la crea
    cur.execute(
        "SELECT id FROM asistencias WHERE empleado_id = %s AND fecha = %s",
        (empleado_id, fecha),
    )
    existente = cur.fetchone()

    try:
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
            flash("Asistencia actualizada mediante ajuste administrativo", "success")
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
            flash("Ajuste de asistencia registrado correctamente", "success")

        mysql.connection.commit()
    except MySQLdb.Error as e:
        flash(f"Error al guardar el ajuste: {e}", "danger")
    finally:
        cur.close()

    return redirect(url_for("asistencias.index"))


@asistencias_bp.route("/eliminar/<int:id>", methods=["POST"])
@login_required
def eliminar(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM asistencias WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    flash("Registro de asistencia eliminado", "info")
    return redirect(url_for("asistencias.index"))
