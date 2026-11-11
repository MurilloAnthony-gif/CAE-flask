from datetime import timedelta
import MySQLdb
from flask import Blueprint, flash, redirect, render_template, request, url_for
from werkzeug.security import generate_password_hash

from db import mysql
from routes.auth import login_required

empleados_bp = Blueprint("empleados", __name__, url_prefix="/empleados")


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


def _cargar_catalogos(cur):
    cur.execute("SELECT id, nombre FROM departamentos WHERE activo = 1 ORDER BY nombre")
    departamentos = cur.fetchall()
    cur.execute("SELECT id, nombre FROM cargos WHERE activo = 1 ORDER BY nombre")
    cargos = cur.fetchall()
    cur.execute("SELECT id, nombre, hora_entrada, hora_salida FROM horarios ORDER BY nombre")
    horarios = cur.fetchall()
    for h in horarios:
        h["hora_entrada"] = _formatear_hora(h["hora_entrada"])
        h["hora_salida"] = _formatear_hora(h["hora_salida"])
    return departamentos, cargos, horarios


@empleados_bp.route("/")
@login_required
def index():
    cur = mysql.connection.cursor()
    cur.execute(
        """
        SELECT e.*,
               d.nombre AS departamento,
               c.nombre AS cargo,
               h.nombre AS horario
        FROM empleados e
        INNER JOIN departamentos d ON d.id = e.departamento_id
        INNER JOIN cargos c ON c.id = e.cargo_id
        INNER JOIN horarios h ON h.id = e.horario_id
        ORDER BY e.id DESC
        """
    )
    empleados = cur.fetchall()
    cur.close()

    return render_template("empleados/index.html", empleados=empleados)


@empleados_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    cur = mysql.connection.cursor()
    departamentos, cargos, horarios = _cargar_catalogos(cur)

    if request.method == "POST":
        cedula = request.form.get("cedula", "").strip()
        nombres = request.form.get("nombres", "").strip()
        apellidos = request.form.get("apellidos", "").strip()
        email = request.form.get("email", "").strip() or None
        telefono = request.form.get("telefono", "").strip() or None
        fecha_ingreso = request.form.get("fecha_ingreso", "").strip()
        pin = request.form.get("pin", "").strip()
        departamento_id = request.form.get("departamento_id")
        cargo_id = request.form.get("cargo_id")
        horario_id = request.form.get("horario_id")
        activo = 1 if request.form.get("activo") else 0

        if not all([cedula, nombres, apellidos, fecha_ingreso, departamento_id, cargo_id, horario_id]):
            flash("Completa todos los campos obligatorios del empleado", "danger")
            cur.close()
            return render_template(
                "empleados/form.html",
                emp=None,
                departamentos=departamentos,
                cargos=cargos,
                horarios=horarios,
            )

        pin_hash = generate_password_hash(pin) if pin else None

        try:
            cur.execute(
                """
                INSERT INTO empleados
                    (cedula, nombres, apellidos, email, telefono, fecha_ingreso,
                     pin_hash, departamento_id, cargo_id, horario_id, activo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    cedula,
                    nombres,
                    apellidos,
                    email,
                    telefono,
                    fecha_ingreso,
                    pin_hash,
                    departamento_id,
                    cargo_id,
                    horario_id,
                    activo,
                ),
            )
            mysql.connection.commit()
            cur.close()
            flash("Empleado registrado correctamente", "success")
            return redirect(url_for("empleados.index"))
        except MySQLdb.IntegrityError:
            cur.close()
            flash("Ya existe un empleado con ese número de cédula", "danger")
            return render_template(
                "empleados/form.html",
                emp=None,
                departamentos=departamentos,
                cargos=cargos,
                horarios=horarios,
            )

    cur.close()
    return render_template(
        "empleados/form.html",
        emp=None,
        departamentos=departamentos,
        cargos=cargos,
        horarios=horarios,
    )


@empleados_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar(id):
    cur = mysql.connection.cursor()
    departamentos, cargos, horarios = _cargar_catalogos(cur)

    if request.method == "POST":
        cedula = request.form.get("cedula", "").strip()
        nombres = request.form.get("nombres", "").strip()
        apellidos = request.form.get("apellidos", "").strip()
        email = request.form.get("email", "").strip() or None
        telefono = request.form.get("telefono", "").strip() or None
        fecha_ingreso = request.form.get("fecha_ingreso", "").strip()
        pin = request.form.get("pin", "").strip()
        departamento_id = request.form.get("departamento_id")
        cargo_id = request.form.get("cargo_id")
        horario_id = request.form.get("horario_id")
        activo = 1 if request.form.get("activo") else 0

        try:
            if pin:
                cur.execute(
                    """
                    UPDATE empleados
                    SET cedula = %s, nombres = %s, apellidos = %s, email = %s,
                        telefono = %s, fecha_ingreso = %s, pin_hash = %s,
                        departamento_id = %s, cargo_id = %s, horario_id = %s, activo = %s
                    WHERE id = %s
                    """,
                    (
                        cedula,
                        nombres,
                        apellidos,
                        email,
                        telefono,
                        fecha_ingreso,
                        generate_password_hash(pin),
                        departamento_id,
                        cargo_id,
                        horario_id,
                        activo,
                        id,
                    ),
                )
            else:
                cur.execute(
                    """
                    UPDATE empleados
                    SET cedula = %s, nombres = %s, apellidos = %s, email = %s,
                        telefono = %s, fecha_ingreso = %s,
                        departamento_id = %s, cargo_id = %s, horario_id = %s, activo = %s
                    WHERE id = %s
                    """,
                    (
                        cedula,
                        nombres,
                        apellidos,
                        email,
                        telefono,
                        fecha_ingreso,
                        departamento_id,
                        cargo_id,
                        horario_id,
                        activo,
                        id,
                    ),
                )
            mysql.connection.commit()
            cur.close()
            flash("Empleado actualizado correctamente", "success")
            return redirect(url_for("empleados.index"))
        except MySQLdb.IntegrityError:
            flash("Ya existe otro empleado con esa cédula", "danger")

    cur.execute("SELECT * FROM empleados WHERE id = %s", (id,))
    emp = cur.fetchone()
    cur.close()

    if not emp:
        flash("Empleado no encontrado", "warning")
        return redirect(url_for("empleados.index"))

    return render_template(
        "empleados/form.html",
        emp=emp,
        departamentos=departamentos,
        cargos=cargos,
        horarios=horarios,
    )


@empleados_bp.route("/eliminar/<int:id>", methods=["POST"])
@login_required
def eliminar(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM empleados WHERE id = %s", (id,))
        mysql.connection.commit()
        cur.close()
        flash("Empleado eliminado correctamente", "success")
    except MySQLdb.IntegrityError:
        flash(
            "No se puede eliminar el empleado porque ya tiene registros de asistencia. "
            "Puedes desactivarlo desde Editar.",
            "danger",
        )

    return redirect(url_for("empleados.index"))
