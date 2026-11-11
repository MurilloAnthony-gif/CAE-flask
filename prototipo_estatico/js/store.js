/* Capa de datos simulada con localStorage.
   Cada colección corresponde a una tabla de MySQL.*/
const Store = {
  seed() {
    if (localStorage.getItem('db_seeded')) return;
    const db = {
      usuarios: [{ id: 1, usuario: 'admin', password: 'admin123', nombre: 'Administrador' }],
      departamentos: [
        { id: 1, nombre: 'Recursos Humanos', descripcion: 'Gestión del personal' },
        { id: 2, nombre: 'Tecnología', descripcion: 'Desarrollo y soporte' }],
      cargos: [
        { id: 1, nombre: 'Analista', descripcion: '' },
        { id: 2, nombre: 'Desarrollador', descripcion: '' },
        { id: 3, nombre: 'Gerente', descripcion: '' }],
      horarios: [
        { id: 1, nombre: 'Matutino', hora_entrada: '08:00', hora_salida: '16:00', tolerancia: 10 },
        { id: 2, nombre: 'Vespertino', hora_entrada: '14:00', hora_salida: '22:00', tolerancia: 10 }],
      empleados: [
        { id: 1, cedula: '0102030405', nombre: 'Ana', apellido: 'Pérez', email: 'ana@empresa.com', telefono: '0991112233',
          fecha_ingreso: '2025-01-15', departamento_id: 1, cargo_id: 1, horario_id: 1 },
        { id: 2, cedula: '0912345678', nombre: 'Luis', apellido: 'Mora', email: 'luis@empresa.com', telefono: '0984445566',
          fecha_ingreso: '2025-03-01', departamento_id: 2, cargo_id: 2, horario_id: 1 }],
      asistencias: [],
    };
    for (const k in db) localStorage.setItem('db_' + k, JSON.stringify(db[k]));
    localStorage.setItem('db_seeded', '1');
  },
  all(t) { return JSON.parse(localStorage.getItem('db_' + t) || '[]'); },
  save(t, rows) { localStorage.setItem('db_' + t, JSON.stringify(rows)); },
  get(t, id) { return this.all(t).find(r => r.id == id); },
  upsert(t, obj) {
    const rows = this.all(t);
    if (obj.id) { const i = rows.findIndex(r => r.id == obj.id); rows[i] = { ...rows[i], ...obj, id: +obj.id }; }
    else { obj.id = rows.reduce((m, r) => Math.max(m, r.id), 0) + 1; rows.push(obj); }
    this.save(t, rows);
    return obj;
  },
  remove(t, id) { this.save(t, this.all(t).filter(r => r.id != id)); },
};
Store.seed();
