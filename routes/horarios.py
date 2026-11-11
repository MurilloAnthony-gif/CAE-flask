import MySQLdb
from flask import Blueprint, flash, redirect, render_template, request, url_for

from db import mysql
from routes.auth import login_required

horarios_bp = Blueprint("horarios", __name__, url_prefix="/horarios")

DIAS_SEMANA = [
    ("1", "Lunes"),
    ("2", "Martes"),
    ("3", "Miércoles"),
    ("4", "Jueves"),
    ("5", "Viernes"),
    ("6", "Sábado"),
    ("7", "Domingo"),
]


@horarios_bp.route("/")
@login_required
def index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM horarios ORDER BY id DESC")
    horarios = cur.fetchall()
    cur.close()
    return render_template("horarios/index.html", horarios=horarios, dias_semana=DIAS_SEMANA)


@horarios_bp.route("/crear", methods=["POST"])
@login_required
def crear():
    nombre = request.form.get("nombre", "").strip()
    hora_entrada = request.form.get("hora_entrada", "").strip()
    hora_salida = request.form.get("hora_salida", "").strip()
    tolerancia_min = request.form.get("tolerancia_min", "10").strip()
    dias_seleccionados = request.form.getlist("dias_laborables")
    dias_laborables = ",".join(dias_seleccionados) if dias_seleccionados else "1,2,3,4,5"

    if not nombre or not hora_entrada or not hora_salida:
        flash("Nombre, hora de entrada y hora de salida son obligatorios", "danger")
        return redirect(url_for("horarios.index"))

    try:
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO horarios (nombre, hora_entrada, hora_salida, tolerancia_min, dias_laborables) "
            "VALUES (%s, %s, %s, %s, %s)",
            (nombre, hora_entrada, hora_salida, int(tolerancia_min), dias_laborables),
        )
        mysql.connection.commit()
        cur.close()
        flash("Horario creado correctamente", "success")
    except (MySQLdb.Error, ValueError) as e:
        flash(f"No se pudo crear el horario (verifica que salida > entrada y nombre único): {e}", "danger")

    return redirect(url_for("horarios.index"))


@horarios_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar(id):
    cur = mysql.connection.cursor()

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        hora_entrada = request.form.get("hora_entrada", "").strip()
        hora_salida = request.form.get("hora_salida", "").strip()
        tolerancia_min = request.form.get("tolerancia_min", "10").strip()
        dias_seleccionados = request.form.getlist("dias_laborables")
        dias_laborables = ",".join(dias_seleccionados) if dias_seleccionados else "1,2,3,4,5"

        try:
            cur.execute(
                "UPDATE horarios SET nombre = %s, hora_entrada = %s, hora_salida = %s, "
                "tolerancia_min = %s, dias_laborables = %s WHERE id = %s",
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

    dias_activos = (horario["dias_laborables"] or "").split(",")
    return render_template(
        "horarios/editar.html",
        horario=horario,
        dias_semana=DIAS_SEMANA,
        dias_activos=dias_activos,
    )


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
