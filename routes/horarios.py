from datetime import timedelta
import MySQLdb
from flask import Blueprint, flash, redirect, render_template, request, url_for

from db import mysql
from routes.auth import login_required

horarios_bp = Blueprint("horarios", __name__, url_prefix="/horarios")

MAPA_NUM_A_LETRA = {"1": "L", "2": "M", "3": "X", "4": "J", "5": "V", "6": "S", "7": "D"}


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


def _normalizar_dias(dias_str):
    if not dias_str:
        return "L,M,X,J,V"
    partes = [p.strip() for p in dias_str.split(",") if p.strip()]
    return ",".join(MAPA_NUM_A_LETRA.get(p, p) for p in partes)


@horarios_bp.route("/")
@login_required
def index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM horarios ORDER BY id DESC")
    horarios = cur.fetchall()
    cur.close()

    for h in horarios:
        h["hora_entrada"] = _formatear_hora(h["hora_entrada"])
        h["hora_salida"] = _formatear_hora(h["hora_salida"])
        h["dias_laborables"] = _normalizar_dias(h["dias_laborables"])

    return render_template("horarios/index.html", horarios=horarios)


@horarios_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        hora_entrada = request.form.get("hora_entrada", "").strip()
        hora_salida = request.form.get("hora_salida", "").strip()
        tolerancia_min = request.form.get("tolerancia_min", "10").strip()
        dias_sel = request.form.getlist("dias")
        dias_laborables = ",".join(dias_sel) if dias_sel else "L,M,X,J,V"

        if not nombre or not hora_entrada or not hora_salida:
            flash("Nombre, hora de entrada y hora de salida son obligatorios", "danger")
            return render_template("horarios/form.html", horario=None)

        try:
            cur = mysql.connection.cursor()
            cur.execute(
                """
                INSERT INTO horarios (nombre, hora_entrada, hora_salida, tolerancia_min, dias_laborables)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (nombre, hora_entrada, hora_salida, int(tolerancia_min), dias_laborables),
            )
            mysql.connection.commit()
            cur.close()
            flash("Horario creado correctamente", "success")
            return redirect(url_for("horarios.index"))
        except (MySQLdb.Error, ValueError) as e:
            flash(f"No se pudo crear el horario (verifica que salida > entrada y nombre único): {e}", "danger")
            return render_template("horarios/form.html", horario=None)

    return render_template("horarios/form.html", horario=None)


@horarios_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar(id):
    cur = mysql.connection.cursor()

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        hora_entrada = request.form.get("hora_entrada", "").strip()
        hora_salida = request.form.get("hora_salida", "").strip()
        tolerancia_min = request.form.get("tolerancia_min", "10").strip()
        dias_sel = request.form.getlist("dias")
        dias_laborables = ",".join(dias_sel) if dias_sel else "L,M,X,J,V"

        try:
            cur.execute(
                """
                UPDATE horarios
                SET nombre = %s, hora_entrada = %s, hora_salida = %s,
                    tolerancia_min = %s, dias_laborables = %s
                WHERE id = %s
                """,
                (nombre, hora_entrada, hora_salida, int(tolerancia_min), dias_laborables, id),
            )
            mysql.connection.commit()
            flash("Horario actualizado correctamente", "success")
            cur.close()
            return redirect(url_for("horarios.index"))
        except (MySQLdb.Error, ValueError) as e:
            flash(f"Error al actualizar el horario: {e}", "danger")

    cur.execute("SELECT * FROM horarios WHERE id = %s", (id,))
    horario = cur.fetchone()
    cur.close()

    if not horario:
        flash("Horario no encontrado", "warning")
        return redirect(url_for("horarios.index"))

    horario["hora_entrada"] = _formatear_hora(horario["hora_entrada"])
    horario["hora_salida"] = _formatear_hora(horario["hora_salida"])
    horario["dias_laborables"] = _normalizar_dias(horario["dias_laborables"])

    return render_template("horarios/form.html", horario=horario)


@horarios_bp.route("/eliminar/<int:id>", methods=["POST"])
@login_required
def eliminar(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM horarios WHERE id = %s", (id,))
        mysql.connection.commit()
        cur.close()
        flash("Horario eliminado correctamente", "success")
    except MySQLdb.IntegrityError:
        flash("No se puede eliminar este horario porque tiene empleados asignados", "danger")

    return redirect(url_for("horarios.index"))
