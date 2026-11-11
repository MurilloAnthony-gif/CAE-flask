from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from db import mysql

auth_bp = Blueprint("auth", __name__)


def login_required(vista):
    """Decorador: obliga a iniciar sesión para entrar a la ruta."""

    @wraps(vista)
    def envoltura(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Debes iniciar sesión", "warning")
            return redirect(url_for("auth.login"))
        return vista(*args, **kwargs)

    return envoltura


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "usuario_id" in session:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT id, username, password_hash, nombre, rol FROM usuarios WHERE username = %s",
            (username,),  # <- tupla con coma (el error del video era usar (id) sin coma)
        )
        usuario = cur.fetchone()
        cur.close()

        if usuario and check_password_hash(usuario["password_hash"], password):
            session.clear()
            session["usuario_id"] = usuario["id"]
            session["usuario_nombre"] = usuario["nombre"]
            session["usuario_rol"] = usuario["rol"]
            flash(f"Bienvenido, {usuario['nombre']}", "success")
            return redirect(url_for("main.dashboard"))

        flash("Usuario o contraseña incorrectos", "danger")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada", "info")
    return redirect(url_for("auth.login"))
