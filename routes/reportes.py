from datetime import date, datetime, timedelta
from flask import Blueprint, render_template, request

from db import mysql
from routes.auth import login_required

reportes_bp = Blueprint("reportes", __name__, url_prefix="/reportes")

MAPA_ISO_A_LETRA = {1: "L", 2: "M", 3: "X", 4: "J", 5: "V", 6: "S", 7: "D"}


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


def _calcular_faltas(cur, fecha_inicio_str, fecha_fin_str, empleado_id=None, departamento_id=None):
    """Calcula las faltas (días laborables según el horario del empleado sin asistencia)."""
    try:
        f_ini = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
        f_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return []

    hoy = date.today()
    if f_fin > hoy:
        f_fin = hoy
    if f_ini > f_fin:
        return []

    sql_emp = """
        SELECT e.id, e.cedula, e.nombres, e.apellidos, e.fecha_ingreso,
               d.nombre AS departamento,
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
        iso_dia = dia_cursor.isoweekday()
        num_dia = str(iso_dia)
        letra_dia = MAPA_ISO_A_LETRA.get(iso_dia, "")
        for emp in empleados:
            dias_emp = [d.strip().upper() for d in (emp["dias_laborables"] or "").split(",")]
            if (num_dia in dias_emp or letra_dia in dias_emp) and dia_cursor >= emp["fecha_ingreso"]:
                if (emp["id"], dia_cursor) not in asistencias_set:
                    faltas.append(
                        {
                            "fecha": _formatear_fecha(dia_cursor),
                            "cedula": emp["cedula"],
                            "empleado": f"{emp['nombres']} {emp['apellidos']}",
                            "departamento": emp["departamento"],
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

    # Aceptar 'desde' o 'fecha_inicio'
    desde = request.args.get("desde") or request.args.get("fecha_inicio") or inicio_mes
    hasta = request.args.get("hasta") or request.args.get("fecha_fin") or hoy_str
    empleado_id = request.args.get("empleado_id", "").strip()
    departamento_id = request.args.get("departamento_id", "").strip()

    cur = mysql.connection.cursor()

    sql = """
        SELECT a.*,
               CONCAT(e.nombres, ' ', e.apellidos) AS empleado,
               d.nombre AS departamento
        FROM asistencias a
        INNER JOIN empleados e ON e.id = a.empleado_id
        INNER JOIN departamentos d ON d.id = e.departamento_id
        WHERE a.fecha BETWEEN %s AND %s
    """
    params = [desde, hasta]

    if empleado_id:
        sql += " AND a.empleado_id = %s"
        params.append(empleado_id)
    if departamento_id:
        sql += " AND e.departamento_id = %s"
        params.append(departamento_id)

    sql += " ORDER BY a.fecha DESC, a.hora_entrada DESC"
    cur.execute(sql, tuple(params))
    registros = cur.fetchall()

    for r in registros:
        r["hora_entrada"] = _formatear_hora(r["hora_entrada"])
        r["hora_salida"] = _formatear_hora(r["hora_salida"])
        r["fecha"] = _formatear_fecha(r["fecha"])

    total_atraso_min = sum(int(r["minutos_atraso"] or 0) for r in registros)

    faltas = _calcular_faltas(
        cur,
        desde,
        hasta,
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
        total_atraso_min=total_atraso_min,
        empleados=empleados,
        departamentos=departamentos,
        filtros={
            "desde": desde,
            "hasta": hasta,
            "empleado_id": empleado_id,
            "departamento_id": departamento_id,
        },
    )
