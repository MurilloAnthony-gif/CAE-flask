from datetime import date, datetime, timedelta

from flask import Blueprint, render_template, request

from db import mysql
from routes.auth import login_required

reportes_bp = Blueprint("reportes", __name__, url_prefix="/reportes")


def _calcular_faltas(cur, fecha_inicio_str, fecha_fin_str, empleado_id=None, departamento_id=None):
    """Calcula las faltas (días laborables según el horario del empleado sin asistencia)."""
    try:
        f_ini = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
        f_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()
    except ValueError:
        return []

    hoy = date.today()
    if f_fin > hoy:
        f_fin = hoy
    if f_ini > f_fin:
        return []

    sql_emp = """
        SELECT e.id, e.cedula, e.nombres, e.apellidos, e.fecha_ingreso,
               d.nombre AS departamento_nombre,
               h.nombre AS horario_nombre, h.dias_laborables
        FROM empleados e
        INNER JOIN departamentos d ON d.id = e.departamento_id
        INNER JOIN horarios h ON h.id = e.horario_id
        WHERE e.activo = 1
    """
    params = []
    if empleado_id:
        sql_emp += " AND e.id = %s"
        params.append(empleado_id)
    if departamento_id:
        sql_emp += " AND e.departamento_id = %s"
        params.append(departamento_id)

    cur.execute(sql_emp, tuple(params))
    empleados = cur.fetchall()

    cur.execute(
        "SELECT empleado_id, fecha FROM asistencias WHERE fecha BETWEEN %s AND %s",
        (f_ini, f_fin),
    )
    asistencias_set = {(r["empleado_id"], r["fecha"]) for r in cur.fetchall()}

    faltas = []
    dia_cursor = f_ini
    while dia_cursor <= f_fin:
        num_dia = str(dia_cursor.isoweekday())  # '1' Lunes .. '7' Domingo
        for emp in empleados:
            dias_emp = [d.strip() for d in (emp["dias_laborables"] or "").split(",")]
            if num_dia in dias_emp and dia_cursor >= emp["fecha_ingreso"]:
                if (emp["id"], dia_cursor) not in asistencias_set:
                    faltas.append(
                        {
                            "fecha": dia_cursor,
                            "cedula": emp["cedula"],
                            "empleado": f"{emp['nombres']} {emp['apellidos']}",
                            "departamento": emp["departamento_nombre"],
                            "horario": emp["horario_nombre"],
                        }
                    )
        dia_cursor += timedelta(days=1)

    return faltas


@reportes_bp.route("/")
@login_required
def index():
    hoy = date.today()
    inicio_mes = hoy.replace(day=1).strftime("%Y-%m-%d")
    hoy_str = hoy.strftime("%Y-%m-%d")

    fecha_inicio = request.args.get("fecha_inicio", inicio_mes)
    fecha_fin = request.args.get("fecha_fin", hoy_str)
    empleado_id = request.args.get("empleado_id", "").strip()
    departamento_id = request.args.get("departamento_id", "").strip()
    solo_atrasos = request.args.get("solo_atrasos", "") == "1"

    cur = mysql.connection.cursor()

    sql = """
        SELECT a.*,
               e.cedula, e.nombres, e.apellidos,
               d.nombre AS departamento_nombre,
               c.nombre AS cargo_nombre,
               u.nombre AS admin_nombre
        FROM asistencias a
        INNER JOIN empleados e ON e.id = a.empleado_id
        INNER JOIN departamentos d ON d.id = e.departamento_id
        INNER JOIN cargos c ON c.id = e.cargo_id
        LEFT JOIN usuarios u ON u.id = a.registrado_por
        WHERE a.fecha BETWEEN %s AND %s
    """
    params = [fecha_inicio, fecha_fin]

    if empleado_id:
        sql += " AND a.empleado_id = %s"
        params.append(empleado_id)
    if departamento_id:
        sql += " AND e.departamento_id = %s"
        params.append(departamento_id)
    if solo_atrasos:
        sql += " AND a.estado = 'ATRASO'"

    sql += " ORDER BY a.fecha DESC, a.hora_entrada DESC"
    cur.execute(sql, tuple(params))
    registros = cur.fetchall()

    total_registros = len(registros)
    total_atrasos = sum(1 for r in registros if r["estado"] == "ATRASO")
    total_minutos_atraso = sum(int(r["minutos_atraso"] or 0) for r in registros)
    total_ajustes = sum(1 for r in registros if r["metodo"] == "AJUSTE")

    faltas = _calcular_faltas(
        cur,
        fecha_inicio,
        fecha_fin,
        empleado_id=empleado_id or None,
        departamento_id=departamento_id or None,
    )

    cur.execute("SELECT id, cedula, nombres, apellidos FROM empleados ORDER BY apellidos, nombres")
    empleados = cur.fetchall()
    cur.execute("SELECT id, nombre FROM departamentos ORDER BY nombre")
    departamentos = cur.fetchall()
    cur.close()

    return render_template(
        "reportes/index.html",
        registros=registros,
        faltas=faltas,
        empleados=empleados,
        departamentos=departamentos,
        filtros={
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "empleado_id": empleado_id,
            "departamento_id": departamento_id,
            "solo_atrasos": solo_atrasos,
        },
        resumen={
            "total_registros": total_registros,
            "total_atrasos": total_atrasos,
            "total_minutos_atraso": total_minutos_atraso,
            "total_ajustes": total_ajustes,
            "total_faltas": len(faltas),
        },
    )
