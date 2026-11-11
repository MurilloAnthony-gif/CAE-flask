import MySQLdb
from flask import Blueprint, flash, redirect, render_template, request, url_for

from db import mysql
from routes.auth import login_required

departamentos_bp = Blueprint("departamentos", __name__, url_prefix="/departamentos")


@departamentos_bp.route("/")
@login_required
def index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM departamentos ORDER BY id DESC")
    departamentos = cur.fetchall()
    cur.close()
    return render_template("departamentos/index.html", departamentos=departamentos)


@departamentos_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        descripcion = request.form.get("descripcion", "").strip() or None
        activo = 1 if request.form.get("activo") else 0

        if not nombre:
            flash("El nombre del departamento es obligatorio", "danger")
            return render_template("departamentos/form.html", dep=None)

        try:
            cur = mysql.connection.cursor()
            cur.execute(
                "INSERT INTO departamentos (nombre, descripcion, activo) VALUES (%s, %s, %s)",
                (nombre, descripcion, activo),
            )
            mysql.connection.commit()
            cur.close()
            flash("Departamento creado correctamente", "success")
            return redirect(url_for("departamentos.index"))
        except MySQLdb.IntegrityError:
            flash("Ya existe un departamento con ese nombre", "danger")
            return render_template("departamentos/form.html", dep=None)

    return render_template("departamentos/form.html", dep=None)


@departamentos_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar(id):
    cur = mysql.connection.cursor()

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        descripcion = request.form.get("descripcion", "").strip() or None
        activo = 1 if request.form.get("activo") else 0

        if not nombre:
            flash("El nombre del departamento es obligatorio", "danger")
            cur.execute("SELECT * FROM departamentos WHERE id = %s", (id,))
            dep = cur.fetchone()
            cur.close()
            return render_template("departamentos/form.html", dep=dep)

        try:
            cur.execute(
                "UPDATE departamentos SET nombre = %s, descripcion = %s, activo = %s WHERE id = %s",
                (nombre, descripcion, activo, id),
            )
            mysql.connection.commit()
            flash("Departamento actualizado correctamente", "success")
            cur.close()
            return redirect(url_for("departamentos.index"))
        except MySQLdb.IntegrityError:
            flash("Ya existe otro departamento con ese nombre", "danger")

    cur.execute("SELECT * FROM departamentos WHERE id = %s", (id,))
    dep = cur.fetchone()
    cur.close()

    if not dep:
        flash("Departamento no encontrado", "warning")
        return redirect(url_for("departamentos.index"))

    return render_template("departamentos/form.html", dep=dep)


@departamentos_bp.route("/eliminar/<int:id>", methods=["POST"])
@login_required
def eliminar(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM departamentos WHERE id = %s", (id,))
        mysql.connection.commit()
        cur.close()
        flash("Departamento eliminado correctamente", "success")
    except MySQLdb.IntegrityError:
        flash(
            "No se puede eliminar este departamento porque tiene empleados asignados",
            "danger",
        )

    return redirect(url_for("departamentos.index"))
