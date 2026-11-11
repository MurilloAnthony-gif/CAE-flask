from datetime import datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for
from werkzeug.security import check_password_hash

from db import mysql

marcador_bp = Blueprint("marcador", __name__)


def _a_timedelta(valor_hora):
    """Convierte un valor TIME de MySQL (timedelta o time o str) a timedelta."""
    if isinstance(valor_hora, timedelta):
        return valor_hora
    if hasattr(valor_hora, "hour"):
        return timedelta(hours=valor_hora.hour, minutes=valor_hora.minute, seconds=valor_hora.second)
    partes = [int(p) for p in str(valor_hora).split(":")]
    return timedelta(hours=partes[0], minutes=partes[1], seconds=partes[2] if len(partes) > 2 else 0)


def calcular_atraso(hora_entrada_real, hora_entrada_horario, tolerancia_min):
    """Calcula minutos de atraso y estado ('PUNTUAL' o 'ATRASO').

    El atraso se mide respecto a la hora de entrada del horario, pero solo
    se considera ATRASO si supera los minutos de tolerancia.
    """
    td_real = _a_timedelta(hora_entrada_real)
    td_horario = _a_timedelta(hora_entrada_horario)
    limite = td_horario + timedelta(minutes=int(tolerancia_min or 0))

    if td_real > limite:
        minutos = int((td_real - td_horario).total_seconds() // 60)
        return max(minutos, 1), "ATRASO"
    return 0, "PUNTUAL"


@marcador_bp.route("/marcar", methods=["GET", "POST"])
def marcar():
    """Pantalla pública del reloj marcador (Cédula + PIN).

    La fecha y la hora se toman directamente del servidor MySQL (CURDATE / CURTIME),
    nunca del navegador, para que el empleado no pueda alterar la hora de llegada.
    """
    if request.method == "POST":
        cedula = request.form.get("cedula", "").strip()
        pin = request.form.get("pin", "").strip()
        tipo = request.form.get("tipo", "ENTRADA").upper()  # ENTRADA | SALIDA

        cur = mysql.connection.cursor()
        cur.execute(
            """
            SELECT e.id, e.nombres, e.apellidos, e.pin_hash, e.activo,
                   h.hora_entrada AS horario_entrada,
                   h.hora_salida  AS horario_salida,
                   h.tolerancia_min,
                   CURDATE() AS fecha_hoy,
                   CURTIME() AS hora_actual
            FROM empleados e
            INNER JOIN horarios h ON h.id = e.horario_id
            WHERE e.cedula = %s
            """,
            (cedula,),
        )
        emp = cur.fetchone()

        if not emp or not emp["activo"]:
            cur.close()
            flash("Cédula no encontrada o empleado inactivo", "danger")
            return redirect(url_for("marcador.marcar"))

        if not emp["pin_hash"] or not check_password_hash(emp["pin_hash"], pin):
            cur.close()
            flash("PIN incorrecto (o el empleado aún no tiene PIN asignado)", "danger")
            return redirect(url_for("marcador.marcar"))

        fecha_hoy = emp["fecha_hoy"]
        hora_actual = emp["hora_actual"]
        nombre_completo = f"{emp['nombres']} {emp['apellidos']}"

        # Consultar si ya existe registro hoy
        cur.execute(
            "SELECT * FROM asistencias WHERE empleado_id = %s AND fecha = %s",
            (emp["id"], fecha_hoy),
        )
        asistencia = cur.fetchone()

        if tipo == "ENTRADA":
            if asistencia and asistencia["hora_entrada"]:
                cur.close()
                flash(
                    f"{nombre_completo}: ya registraste tu entrada hoy a las {asistencia['hora_entrada']}",
                    "warning",
                )
                return redirect(url_for("marcador.marcar"))

            minutos_atraso, estado = calcular_atraso(
                hora_actual, emp["horario_entrada"], emp["tolerancia_min"]
            )

            cur.execute(
                """
                INSERT INTO asistencias
                    (empleado_id, fecha, hora_entrada, minutos_atraso, estado, metodo)
                VALUES (%s, %s, %s, %s, %s, 'PIN')
                """,
                (emp["id"], fecha_hoy, hora_actual, minutos_atraso, estado),
            )
            mysql.connection.commit()
            cur.close()

            detalle = f"Atraso: {minutos_atraso} min" if estado == "ATRASO" else "Puntual"
            flash(
                f"Entrada registrada — {nombre_completo} a las {hora_actual} ({detalle})",
                "success" if estado == "PUNTUAL" else "warning",
            )
            return redirect(url_for("marcador.marcar"))

        elif tipo == "SALIDA":
            if not asistencia or not asistencia["hora_entrada"]:
                cur.close()
                flash(
                    f"{nombre_completo}: primero debes registrar tu ENTRADA de hoy",
                    "danger",
                )
                return redirect(url_for("marcador.marcar"))

            if asistencia["hora_salida"]:
                cur.close()
                flash(
                    f"{nombre_completo}: ya registraste tu salida hoy a las {asistencia['hora_salida']}",
                    "warning",
                )
                return redirect(url_for("marcador.marcar"))

            cur.execute(
                "UPDATE asistencias SET hora_salida = %s WHERE id = %s",
                (hora_actual, asistencia["id"]),
            )
            mysql.connection.commit()
            cur.close()
            flash(f"Salida registrada — {nombre_completo} a las {hora_actual}", "success")
            return redirect(url_for("marcador.marcar"))

        cur.close()

    ahora_servidor = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return render_template("marcar.html", ahora_servidor=ahora_servidor)
