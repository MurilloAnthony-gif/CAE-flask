const $ = (s, r = document) => r.querySelector(s);
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const today = () => new Date().toLocaleDateString('en-CA');
const nowTime = () => new Date().toTimeString().slice(0, 5);
const toMin = t => { const [h, m] = t.split(':'); return +h * 60 + +m; };
const nameOf = (t, id, f = 'nombre') => Store.get(t, id)?.[f] ?? '—';
const empName = id => { const e = Store.get('empleados', id); return e ? `${e.nombre} ${e.apellido}` : '—'; };

/* ---------- Modal ---------- */
function openModal(html) { $('#modal-body').innerHTML = html; $('#modal').classList.remove('hidden'); }
function closeModal() { $('#modal').classList.add('hidden'); }
$('#modal').addEventListener('click', e => { if (e.target.id === 'modal') closeModal(); });

/* ---------- Auth ---------- */
const session = () => sessionStorage.getItem('user');
$('#login-form').addEventListener('submit', e => {
  e.preventDefault();
  const f = new FormData(e.target);
  const u = Store.all('usuarios').find(u => u.usuario === f.get('usuario') && u.password === f.get('password'));
  if (!u) { $('#login-error').textContent = 'Usuario o contraseña incorrectos'; return; }
  sessionStorage.setItem('user', u.nombre); $('#login-error').textContent = ''; e.target.reset(); render();
});
$('#logout').addEventListener('click', () => { sessionStorage.removeItem('user'); render(); });

/* ---------- CRUD genérico simple (departamentos, cargos, horarios) ---------- */
function simpleCrud(table, title, fields, cols) {
  const rows = Store.all(table);
  $('#main').innerHTML = `
    <div class="head"><h1>${title}</h1><button class="btn primary" id="add">+ Nuevo</button></div>
    <table><thead><tr>${cols.map(c => `<th>${c.label}</th>`).join('')}<th></th></tr></thead><tbody>
    ${rows.map(r => `<tr>${cols.map(c => `<td>${esc(c.fmt ? c.fmt(r) : r[c.key])}</td>`).join('')}
      <td class="actions"><button class="btn sm" data-edit="${r.id}">Editar</button>
      <button class="btn sm danger" data-del="${r.id}">Eliminar</button></td></tr>`).join('')
      || `<tr><td class="empty" colspan="${cols.length + 1}">Sin registros</td></tr>`}</tbody></table>`;
  const form = (r = {}) => {
    openModal(`<h3>${r.id ? 'Editar' : 'Nuevo'} registro</h3><form id="f"><div class="form-grid">
      ${fields.map(f => `<label class="${f.full ? 'full' : ''}">${f.label}
        <input name="${f.key}" type="${f.type || 'text'}" value="${esc(r[f.key])}" ${f.req === false ? '' : 'required'}></label>`).join('')}
      </div><div class="modal-actions"><button type="button" class="btn" onclick="closeModal()">Cancelar</button>
      <button class="btn primary">Guardar</button></div></form>`);
    $('#f').onsubmit = e => {
      e.preventDefault();
      const o = Object.fromEntries(new FormData(e.target));
      if (r.id) o.id = r.id;
      if (o.tolerancia !== undefined) o.tolerancia = +o.tolerancia;
      Store.upsert(table, o); closeModal(); render();
    };
  };
  $('#add').onclick = () => form();
  document.querySelectorAll('[data-edit]').forEach(b => b.onclick = () => form(Store.get(table, b.dataset.edit)));
  document.querySelectorAll('[data-del]').forEach(b => b.onclick = () => {
    const id = b.dataset.del;
    const fk = { departamentos: 'departamento_id', cargos: 'cargo_id', horarios: 'horario_id' }[table];
    if (Store.all('empleados').some(e => e[fk] == id)) return alert('No se puede eliminar: hay empleados asociados.');
    if (confirm('¿Eliminar este registro?')) { Store.remove(table, id); render(); }
  });
}

/* ---------- Vistas ---------- */
const views = {
  dashboard() {
    const as = Store.all('asistencias').filter(a => a.fecha === today());
    $('#main').innerHTML = `<div class="head"><h1>Bienvenido, ${esc(session())}</h1><span class="muted">${today()}</span></div>
      <div class="grid">
        <div class="card stat"><b>${Store.all('empleados').length}</b>Empleados</div>
        <div class="card stat"><b>${Store.all('departamentos').length}</b>Departamentos</div>
        <div class="card stat"><b>${as.length}</b>Asistencias hoy</div>
        <div class="card stat"><b>${as.filter(a => a.atraso > 0).length}</b>Atrasos hoy</div>
      </div>`;
  },
  departamentos() {
    simpleCrud('departamentos', 'Departamentos',
      [{ key: 'nombre', label: 'Nombre' }, { key: 'descripcion', label: 'Descripción', req: false, full: true }],
      [{ key: 'nombre', label: 'Nombre' }, { key: 'descripcion', label: 'Descripción' }]);
  },
  cargos() {
    simpleCrud('cargos', 'Cargos',
      [{ key: 'nombre', label: 'Nombre' }, { key: 'descripcion', label: 'Descripción', req: false, full: true }],
      [{ key: 'nombre', label: 'Nombre' }, { key: 'descripcion', label: 'Descripción' }]);
  },
  horarios() {
    simpleCrud('horarios', 'Horarios de trabajo',
      [{ key: 'nombre', label: 'Nombre', full: true }, { key: 'hora_entrada', label: 'Hora entrada', type: 'time' },
       { key: 'hora_salida', label: 'Hora salida', type: 'time' }, { key: 'tolerancia', label: 'Tolerancia (min)', type: 'number' }],
      [{ key: 'nombre', label: 'Nombre' }, { key: 'hora_entrada', label: 'Entrada' }, { key: 'hora_salida', label: 'Salida' },
       { key: 'tolerancia', label: 'Tolerancia', fmt: r => r.tolerancia + ' min' }]);
  },
  empleados() {
    const rows = Store.all('empleados');
    $('#main').innerHTML = `
      <div class="head"><h1>Empleados</h1><button class="btn primary" id="add">+ Nuevo empleado</button></div>
      <table><thead><tr><th>Cédula</th><th>Nombre</th><th>Departamento</th><th>Cargo</th><th>Horario</th><th>Email</th><th></th></tr></thead><tbody>
      ${rows.map(e => `<tr><td>${esc(e.cedula)}</td><td>${esc(e.nombre + ' ' + e.apellido)}</td>
        <td>${esc(nameOf('departamentos', e.departamento_id))}</td><td>${esc(nameOf('cargos', e.cargo_id))}</td>
        <td>${esc(nameOf('horarios', e.horario_id))}</td><td>${esc(e.email)}</td>
        <td class="actions"><button class="btn sm" data-edit="${e.id}">Editar</button>
        <button class="btn sm danger" data-del="${e.id}">Eliminar</button></td></tr>`).join('')
        || '<tr><td class="empty" colspan="7">Sin empleados</td></tr>'}</tbody></table>`;
    const opts = (t, sel) => Store.all(t).map(o => `<option value="${o.id}" ${o.id == sel ? 'selected' : ''}>${esc(o.nombre)}</option>`).join('');
    const form = (e = {}) => {
      openModal(`<h3>${e.id ? 'Editar' : 'Nuevo'} empleado</h3><form id="f"><div class="form-grid">
        <label>Cédula<input name="cedula" required pattern="\\d{10}" title="10 dígitos" value="${esc(e.cedula)}"></label>
        <label>Fecha de ingreso<input name="fecha_ingreso" type="date" required value="${esc(e.fecha_ingreso)}"></label>
        <label>Nombre<input name="nombre" required value="${esc(e.nombre)}"></label>
        <label>Apellido<input name="apellido" required value="${esc(e.apellido)}"></label>
        <label>Email<input name="email" type="email" value="${esc(e.email)}"></label>
        <label>Teléfono<input name="telefono" value="${esc(e.telefono)}"></label>
        <label>Departamento<select name="departamento_id" required>${opts('departamentos', e.departamento_id)}</select></label>
        <label>Cargo<select name="cargo_id" required>${opts('cargos', e.cargo_id)}</select></label>
        <label class="full">Horario<select name="horario_id" required>${opts('horarios', e.horario_id)}</select></label>
        </div><div class="modal-actions"><button type="button" class="btn" onclick="closeModal()">Cancelar</button>
        <button class="btn primary">Guardar</button></div></form>`);
      $('#f').onsubmit = ev => {
        ev.preventDefault();
        const o = Object.fromEntries(new FormData(ev.target));
        ['departamento_id', 'cargo_id', 'horario_id'].forEach(k => o[k] = +o[k]);
        if (Store.all('empleados').some(x => x.cedula === o.cedula && x.id != e.id)) return alert('La cédula ya está registrada.');
        if (e.id) o.id = e.id;
        Store.upsert('empleados', o); closeModal(); render();
      };
    };
    $('#add').onclick = () => form();
    document.querySelectorAll('[data-edit]').forEach(b => b.onclick = () => form(Store.get('empleados', b.dataset.edit)));
    document.querySelectorAll('[data-del]').forEach(b => b.onclick = () => {
      if (confirm('¿Eliminar empleado y sus asistencias?')) {
        Store.remove('empleados', b.dataset.del);
        Store.save('asistencias', Store.all('asistencias').filter(a => a.empleado_id != b.dataset.del));
        render();
      }
    });
  },
  asistencias() {
    const emps = Store.all('empleados');
    $('#main').innerHTML = `<div class="head"><h1>Marcar asistencia manual</h1></div>
      <form id="f" class="card form-grid">
        <label>Empleado<select name="empleado_id" required>${emps.map(e => `<option value="${e.id}">${esc(e.nombre + ' ' + e.apellido)}</option>`).join('')}</select></label>
        <label>Fecha<input type="date" name="fecha" value="${today()}" required></label>
        <label>Tipo<select name="tipo"><option value="entrada">Entrada</option><option value="salida">Salida</option></select></label>
        <label>Hora<input type="time" name="hora" value="${nowTime()}" required></label>
        <div class="full"><button class="btn primary">Registrar</button></div>
      </form>
      <h3>Registros de hoy</h3><div id="today"></div>`;
    const paint = () => {
      const rows = Store.all('asistencias').filter(a => a.fecha === today());
      $('#today').innerHTML = `<table><thead><tr><th>Empleado</th><th>Entrada</th><th>Salida</th><th>Atraso</th></tr></thead><tbody>
        ${rows.map(a => `<tr><td>${esc(empName(a.empleado_id))}</td><td>${a.hora_entrada || '—'}</td><td>${a.hora_salida || '—'}</td>
        <td>${a.atraso > 0 ? `<span class="badge late">${a.atraso} min</span>` : '<span class="badge ok">Puntual</span>'}</td></tr>`).join('')
        || '<tr><td class="empty" colspan="4">Sin registros hoy</td></tr>'}</tbody></table>`;
    };
    paint();
    $('#f').onsubmit = ev => {
      ev.preventDefault();
      const f = Object.fromEntries(new FormData(ev.target));
      const id = +f.empleado_id, emp = Store.get('empleados', id), h = Store.get('horarios', emp.horario_id);
      let rec = Store.all('asistencias').find(a => a.empleado_id === id && a.fecha === f.fecha);
      if (f.tipo === 'entrada') {
        if (rec?.hora_entrada) return alert('Ya existe una entrada para ese día.');
        const atraso = Math.max(0, toMin(f.hora) - toMin(h.hora_entrada) - h.tolerancia);
        Store.upsert('asistencias', { ...(rec || { empleado_id: id, fecha: f.fecha }), hora_entrada: f.hora, atraso });
      } else {
        if (!rec?.hora_entrada) return alert('Primero registra la entrada.');
        if (rec.hora_salida) return alert('Ya existe una salida para ese día.');
        if (toMin(f.hora) <= toMin(rec.hora_entrada)) return alert('La salida debe ser posterior a la entrada.');
        Store.upsert('asistencias', { ...rec, hora_salida: f.hora });
      }
      paint();
    };
  },
  reportes() {
    const first = today().slice(0, 8) + '01';
    $('#main').innerHTML = `<div class="head"><h1>Reportes de asistencia</h1><button class="btn" id="csv">Exportar CSV</button></div>
      <form id="f" class="filters">
        <label>Desde<input type="date" name="desde" value="${first}"></label>
        <label>Hasta<input type="date" name="hasta" value="${today()}"></label>
        <label>Empleado<select name="emp"><option value="">Todos</option>${Store.all('empleados').map(e => `<option value="${e.id}">${esc(e.nombre + ' ' + e.apellido)}</option>`).join('')}</select></label>
        <label>Mostrar<select name="solo"><option value="">Todas</option><option value="atrasos">Solo atrasos</option></select></label>
      </form>
      <div class="grid" id="sum"></div><div id="out"></div>`;
    let current = [];
    const paint = () => {
      const f = Object.fromEntries(new FormData($('#f')));
      current = Store.all('asistencias').filter(a =>
        (!f.desde || a.fecha >= f.desde) && (!f.hasta || a.fecha <= f.hasta) &&
        (!f.emp || a.empleado_id == f.emp) && (f.solo !== 'atrasos' || a.atraso > 0))
        .sort((a, b) => b.fecha.localeCompare(a.fecha));
      const late = current.filter(a => a.atraso > 0);
      $('#sum').innerHTML = `<div class="card stat"><b>${current.length}</b>Registros</div>
        <div class="card stat"><b>${late.length}</b>Atrasos</div>
        <div class="card stat"><b>${late.reduce((s, a) => s + a.atraso, 0)}</b>Minutos de atraso</div>`;
      $('#out').innerHTML = `<table><thead><tr><th>Fecha</th><th>Empleado</th><th>Departamento</th><th>Entrada</th><th>Salida</th><th>Estado</th></tr></thead><tbody>
        ${current.map(a => { const e = Store.get('empleados', a.empleado_id);
          return `<tr><td>${a.fecha}</td><td>${esc(empName(a.empleado_id))}</td><td>${esc(nameOf('departamentos', e?.departamento_id))}</td>
          <td>${a.hora_entrada || '—'}</td><td>${a.hora_salida || '—'}</td>
          <td>${a.atraso > 0 ? `<span class="badge late">Atraso ${a.atraso} min</span>` : '<span class="badge ok">Puntual</span>'}</td></tr>`; }).join('')
          || '<tr><td class="empty" colspan="6">Sin resultados</td></tr>'}</tbody></table>`;
    };
    $('#f').addEventListener('input', paint); paint();
    $('#csv').onclick = () => {
      const lines = [['Fecha', 'Empleado', 'Entrada', 'Salida', 'Atraso(min)'],
        ...current.map(a => [a.fecha, empName(a.empleado_id), a.hora_entrada || '', a.hora_salida || '', a.atraso])];
      const blob = new Blob(['\ufeff' + lines.map(l => l.map(c => `"${c}"`).join(',')).join('\n')], { type: 'text/csv' });
      const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'reporte_asistencia.csv'; a.click();
    };
  },
};

/* ---------- Router ---------- */
function render() {
  const logged = !!session();
  $('#login-view').classList.toggle('hidden', logged);
  $('#app-view').classList.toggle('hidden', !logged);
  if (!logged) return;
  const route = location.hash.slice(1) in views ? location.hash.slice(1) : 'dashboard';
  document.querySelectorAll('#nav a').forEach(a => a.classList.toggle('active', a.hash === '#' + route));
  views[route]();
}
window.addEventListener('hashchange', render);
render();
