# Sistema CAE – Control de Asistencia de Empleados

Python + Flask + MySQL.

## Cómo ejecutarlo

1. **Base de datos:** abre `database/cae_db.sql` en MySQL Workbench y ejecútalo completo (⚡).
2. **Contraseña de MySQL:** ponla en `config.py` → `MYSQL_PASSWORD`.
3. **Entorno virtual e instalación** (en la carpeta del proyecto):
   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. **Ejecutar:**
   ```bash
   python app.py
   ```
5. Abre http://localhost:3000
   - Usuario por defecto: `admin` / `admin123` (se crea solo la primera vez).
   - Prueba de conexión: http://localhost:3000/estado-db

## Estructura

```
app.py            crea la app y registra las rutas
config.py         conexión MySQL y SECRET_KEY
db.py             objeto mysql compartido + creación del admin
routes/           lógica (backend), un archivo por módulo
templates/        vistas HTML (frontend)
database/         script SQL
```
