import MySQLdb
from flask import Blueprint, flash, redirect, render_template, request, url_for

from db import mysql
from routes.auth import login_required

cargos_bp = Blueprint("cargos", __name__, url_prefix="/cargos")


@cargos_bp.route("/")
@login_required
def index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM cargos ORDER BY id DESC")
    cargos = cur.fetchall()
    cur.close()
    return render_template("cargos/index.html", cargos=cargos)


@cargos_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        descripcion = request.form.get("descripcion", "").strip() or None
        salario_base = request.form.get("salario_base", "0").strip()
        activo = 1 if request.form.get("activo") else 0

        if not nombre:
            flash("El nombre del cargo es obligatorio", "danger")
            return render_template("cargos/form.html", cargo=None)

        try:
            salario_val = float(salario_base) if salario_base else 0.0
        except ValueError:
            flash("El salario base debe ser un número válido", "danger")
            return render_template("cargos/form.html", cargo=None)

        try:
            cur = mysql.connection.cursor()
            cur.execute(
                "INSERT INTO cargos (nombre, descripcion, salario_base, activo) VALUES (%s, %s, %s, %s)",
                (nombre, descripcion, salario_val, activo),
            )
            mysql.connection.commit()
            cur.close()
            flash("Cargo creado correctamente", "success")
            return redirect(url_for("cargos.index"))
        except MySQLdb.IntegrityError:
            flash("Ya existe un cargo con ese nombre", "danger")
            return render_template("cargos/form.html", cargo=None)

    return render_template("cargos/form.html", cargo=None)


@cargos_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar(id):
    cur = mysql.connection.cursor()

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        descripcion = request.form.get("descripcion", "").strip() or None
        salario_base = request.form.get("salario_base", "0").strip()
        activo = 1 if request.form.get("activo") else 0

        if not nombre:
            flash("El nombre del cargo es obligatorio", "danger")
            cur.execute("SELECT * FROM cargos WHERE id = %s", (id,))
            cargo = cur.fetchone()
            cur.close()
            return render_template("cargos/form.html", cargo=cargo)

        try:
            salario_val = float(salario_base) if salario_base else 0.0
        except ValueError:
            flash("El salario base debe ser un número válido", "danger")
            cur.execute("SELECT * FROM cargos WHERE id = %s", (id,))
            cargo = cur.fetchone()
            cur.close()
            return render_template("cargos/form.html", cargo=cargo)

        try:
            cur.execute(
                "UPDATE cargos SET nombre = %s, descripcion = %s, salario_base = %s, activo = %s WHERE id = %s",
                (nombre, descripcion, salario_val, activo, id),
            )
            mysql.connection.commit()
            flash("Cargo actualizado correctamente", "success")
            cur.close()
            return redirect(url_for("cargos.index"))
        except MySQLdb.IntegrityError:
            flash("Ya existe otro cargo con ese nombre", "danger")

    cur.execute("SELECT * FROM cargos WHERE id = %s", (id,))
    cargo = cur.fetchone()
    cur.close()

    if not cargo:
        flash("Cargo no encontrado", "warning")
        return redirect(url_for("cargos.index"))

    return render_template("cargos/form.html", cargo=cargo)


@cargos_bp.route("/eliminar/<int:id>", methods=["POST"])
@login_required
def eliminar(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM cargos WHERE id = %s", (id,))
        mysql.connection.commit()
        cur.close()
        flash("Cargo eliminado correctamente", "success")
    except MySQLdb.IntegrityError:
        flash(
            "No se puede eliminar este cargo porque tiene empleados asignados",
            "danger",
        )

    return redirect(url_for("cargos.index"))
