# FreshMart ERP API (Open Source)

Backend para gestion de minimarket construido con FastAPI + SQLite, con autenticacion JWT, control de inventario, ventas, proveedores, ordenes y turnos.

## Estado del proyecto

- Estado actual: funcional para uso local y pruebas
- Tipo de proyecto: API backend con vista HTML inicial (`/`)
- Base de datos: SQLite (`database.db`)
- Licencia: pendiente de definicion (se recomienda MIT)

## Stack tecnico

- Python 3.10+
- FastAPI
- Uvicorn
- SQLite3
- PyJWT
- Pydantic

Dependencias actuales en `requirements.txt`:

- `fastapi[standard]`
- `PyJWT`
- `pydantic`
- `python-multipart`

## Estructura del proyecto

```text
local_first/
|- main.py           # API principal (rutas, auth, logica de negocio)
|- init_db.py        # crea tablas y carga datos de ejemplo
|- requirements.txt
|- templates/
|  \- index.html     # vista inicial servida por FastAPI
|- database.py       # archivo de prueba/conexion minima
\- database.db       # se genera localmente (ignorado por git)
```

## Arquitectura funcional

- **Autenticacion y autorizacion**
  - Login con usuario/password
  - Emision de JWT (HS256)
  - Middleware de seguridad via `HTTPBearer`
  - Roles: `admin`, `supervisor`, `cajero`
- **Modulos de negocio**
  - Usuarios
  - Productos e inventario
  - Proveedores
  - Ordenes de compra
  - Ventas y detalle de ventas
  - Turnos
  - Dashboard operativo
- **Persistencia**
  - Acceso a BD con `sqlite3` y contexto transaccional (`get_db`)
  - Esquema definido e inicializado por `init_db.py`

## Modelo de datos (resumen)

Tablas principales:

- `usuarios`
- `productos`
- `proveedores`
- `ordenes`
- `ventas`
- `detalle_ventas`
- `turnos`
- `reposiciones`

Notas:

- Integridad referencial activada con `PRAGMA foreign_keys = ON`.
- `init_db.py` inserta datos de ejemplo solo si las tablas estan vacias.

## API principal

Base URL local: `http://127.0.0.1:8000`

Endpoints relevantes:

- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/change-password`
- `GET/POST/PATCH/DELETE /api/usuarios`
- `GET/POST/PATCH/DELETE /api/productos`
- `POST /api/productos/{pid}/restock`
- `GET/POST/PATCH/DELETE /api/proveedores`
- `GET/POST/PATCH/DELETE /api/ordenes`
- `GET/POST /api/ventas`
- `GET /api/ventas/{vid}/detalle`
- `GET/POST/PATCH/DELETE /api/turnos`
- `GET /api/dashboard`
- `GET /api/health`

Documentacion interactiva (Swagger):

- `http://127.0.0.1:8000/docs`

## Instalacion y ejecucion local

1) Crear entorno virtual:

```bash
python -m venv .venv
```

2) Activar entorno virtual:

- PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

3) Instalar dependencias:

```bash
pip install -r requirements.txt
```

4) Inicializar base de datos:

```bash
python init_db.py
```

5) Ejecutar servidor:

```bash
uvicorn main:app --reload --port 8000
```

## Configuracion

Variables de entorno:

- `FRESHMART_SECRET`: clave para firmar JWT.

Si no se define, el proyecto usa una clave por defecto en codigo. Para uso publico/open source, se recomienda configurar esta variable siempre en desarrollo y produccion.

## Seguridad y hardening recomendado

Antes de publicar o desplegar:

- Cambiar la clave JWT por defecto usando `FRESHMART_SECRET`.
- No usar credenciales de ejemplo en entornos reales.
- Restringir CORS (`allow_origins`) en vez de `*`.
- Agregar rate limiting y auditoria de eventos sensibles.
- Evaluar migrar a PostgreSQL para produccion multiusuario.

## Limitaciones conocidas

- Actualmente no hay carpeta `static/` incluida; si FastAPI falla al iniciar por este punto, crear directorio vacio `static`.
- No hay suite de tests automatizados incluida en esta version.
- El proyecto esta optimizado para ejecucion local/single-node.

## Roadmap sugerido (open source)

- [ ] Tests unitarios e integracion
- [ ] Dockerfile + docker-compose
- [ ] Migraciones de BD (Alembic)
- [ ] CI (lint + test) con GitHub Actions
- [ ] Versionado semantico y changelog

## Contribuciones

Se aceptan issues y pull requests.

Flujo recomendado:

1. Fork del repositorio
2. Crear rama feature/fix
3. Commit con cambios atomicos
4. Abrir Pull Request con descripcion tecnica y pasos de prueba

## Licencia

Este repositorio esta listo para publicarse como open source.  
Define la licencia en este archivo y agrega un archivo `LICENSE` en la raiz.

Ejemplo recomendado:

- MIT License

