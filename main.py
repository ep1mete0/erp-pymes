"""
FreshMart ERP — Backend API (FastAPI + SQLite)
Iniciar: uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
import hashlib
import jwt
import os
import re
import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta, date
from contextlib import contextmanager

# ─── CONFIG ──────────────────────────────────────────────────────
SECRET_KEY = os.getenv("FRESHMART_SECRET", "")
ALGORITHM = "HS256"
TOKEN_EXP = 60 * 12  # 12 horas en minutos
DB_PATH = "database.db"

app = FastAPI(title="FreshMart ERP API", version="1.0.0")
security = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── FRONTEND ──────────────────────────────────────────────────

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={}
    )


# ─── DB HELPERS ──────────────────────────────────────────────────


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def row_to_dict(row) -> dict:
    return dict(row) if row else None


def rows_to_list(rows) -> list:
    return [dict(r) for r in rows]


# ─── CONFIG HELPERS ──────────────────────────────────────────────

def get_config(conn, clave: str) -> str:
    """Lee un valor de la tabla config. Retorna '' si no existe."""
    row = conn.execute(
        "SELECT valor FROM config WHERE clave=?", (clave,)
    ).fetchone()
    return row["valor"] if row else ""


def set_config(conn, clave: str, valor: str):
    conn.execute(
        "INSERT INTO config (clave, valor) VALUES (?,?) "
        "ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor",
        (clave, valor)
    )


# ─── EMAIL ───────────────────────────────────────────────────────

def _build_stock_email(productos: list) -> tuple[str, str]:
    """Construye subject y body HTML para alerta de stock mínimo."""
    subject = f"⚠️ FreshMart — {len(productos)} producto(s) bajo stock mínimo"

    rows_html = "".join(
        f"""
        <tr>
          <td style="padding:10px 14px;border-bottom:1px solid #e5e7eb">{p['icono']} {p['nombre']}</td>
          <td style="padding:10px 14px;border-bottom:1px solid #e5e7eb;text-align:center">{p['categoria']}</td>
          <td style="padding:10px 14px;border-bottom:1px solid #e5e7eb;text-align:center;color:#ef4444;font-weight:700">{p['stock']}</td>
          <td style="padding:10px 14px;border-bottom:1px solid #e5e7eb;text-align:center;color:#6b7280">{p['stock_min']}</td>
        </tr>"""
        for p in productos
    )

    body = f"""
    <div style="font-family:'Segoe UI',Arial,sans-serif;max-width:600px;margin:0 auto;background:#f9fafb;padding:24px">
      <div style="background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.08)">
        <!-- Header -->
        <div style="background:#16a34a;padding:24px 28px">
          <h1 style="margin:0;color:#fff;font-size:20px;font-weight:800">🛒 FreshMart ERP</h1>
          <p style="margin:6px 0 0;color:#dcfce7;font-size:14px">Alerta de stock mínimo</p>
        </div>
        <!-- Body -->
        <div style="padding:24px 28px">
          <p style="color:#374151;font-size:15px;margin:0 0 20px">
            Los siguientes productos han alcanzado o superado su límite de
            <strong>stock mínimo</strong> y requieren reposición inmediata:
          </p>
          <table style="width:100%;border-collapse:collapse;font-size:13px">
            <thead>
              <tr style="background:#f3f4f6">
                <th style="padding:10px 14px;text-align:left;color:#6b7280;font-weight:600">Producto</th>
                <th style="padding:10px 14px;text-align:center;color:#6b7280;font-weight:600">Categoría</th>
                <th style="padding:10px 14px;text-align:center;color:#6b7280;font-weight:600">Stock actual</th>
                <th style="padding:10px 14px;text-align:center;color:#6b7280;font-weight:600">Stock mínimo</th>
              </tr>
            </thead>
            <tbody>{rows_html}</tbody>
          </table>
          <div style="margin-top:24px;padding:14px 18px;background:#fef9c3;border:1px solid #fde047;border-radius:8px">
            <p style="margin:0;color:#713f12;font-size:13px">
              ⚡ Ingresa al sistema y utiliza la sección <strong>Inventario → Ingresar stock</strong>
              o crea una nueva orden en <strong>Proveedores</strong> para reponer estos productos.
            </p>
          </div>
        </div>
        <!-- Footer -->
        <div style="padding:16px 28px;background:#f3f4f6;border-top:1px solid #e5e7eb">
          <p style="margin:0;color:#9ca3af;font-size:12px">
            Este correo fue enviado automáticamente por FreshMart ERP ·
            {datetime.now().strftime('%d/%m/%Y %H:%M')}
          </p>
        </div>
      </div>
    </div>
    """
    return subject, body


def send_email(smtp_email: str, smtp_app_password: str, to_email: str,
               subject: str, body_html: str):
    """Envía un email via Gmail SMTP (puerto 587 + TLS). Lanza excepción si falla."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"FreshMart ERP <{smtp_email}>"
    msg["To"] = to_email
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as server:
        server.ehlo()
        server.starttls()
        server.login(smtp_email, smtp_app_password)
        server.sendmail(smtp_email, to_email, msg.as_string())


def _check_and_notify_stock(productos_ids: list):
    """
    Revisa si alguno de los productos_ids quedó bajo stock mínimo tras una venta.
    Si hay credenciales SMTP configuradas, envía email en un hilo separado
    (no bloquea la respuesta al cajero).
    """
    with get_db() as conn:
        smtp_email = get_config(conn, "smtp_email")
        smtp_pass = get_config(conn, "smtp_app_password")
        notif_dest = get_config(conn, "notif_email_admin")

        if not (smtp_email and smtp_pass and notif_dest):
            return  # Sin config → silencioso

        placeholders = ",".join("?" * len(productos_ids))
        productos_bajos = rows_to_list(conn.execute(
            f"""SELECT id, nombre, categoria, icono, stock, stock_min
                FROM productos
                WHERE id IN ({placeholders})
                  AND activo=1
                  AND stock <= stock_min""",
            productos_ids
        ).fetchall())

    if not productos_bajos:
        return

    def _send():
        try:
            subject, body = _build_stock_email(productos_bajos)
            send_email(smtp_email, smtp_pass, notif_dest, subject, body)
        except Exception:
            pass  # Fallo silencioso en background

    threading.Thread(target=_send, daemon=True).start()


def hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# ─── JWT ─────────────────────────────────────────────────────────


def create_token(user_id: int, rol: str) -> str:
    payload = {
        "sub": str(user_id),
        "rol": rol,
        "exp": datetime.utcnow() + timedelta(minutes=TOKEN_EXP),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_token(credentials.credentials)
    with get_db() as conn:
        user = row_to_dict(conn.execute(
            "SELECT * FROM usuarios WHERE id=? AND activo=1", (payload["sub"],)
        ).fetchone())
    if not user:
        raise HTTPException(
            status_code=401, detail="Usuario no encontrado o desactivado")
    return user


def require_admin(user=Depends(get_current_user)):
    if user["rol"] != "admin":
        raise HTTPException(status_code=403, detail="Se requiere rol admin")
    return user


def require_supervisor(user=Depends(get_current_user)):
    if user["rol"] not in ("admin", "supervisor"):
        raise HTTPException(
            status_code=403, detail="Se requiere rol supervisor o admin")
    return user

# ══════════════════════════════════════════════════════════════════
# SCHEMAS
# ══════════════════════════════════════════════════════════════════


class LoginRequest(BaseModel):
    usuario: str
    password: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


class UsuarioCreate(BaseModel):
    nombre: str
    usuario: str
    password: str
    rol: str
    pin: str = "0000"
    activo: bool = True


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    usuario: Optional[str] = None
    password: Optional[str] = None
    rol: Optional[str] = None
    pin: Optional[str] = None
    activo: Optional[bool] = None


class ProductoCreate(BaseModel):
    id: str
    nombre: str
    categoria: str
    icono: str = "📦"
    precio: float
    costo: float
    stock: int
    stock_min: int
    vencimiento: Optional[str] = None
    descuento: float = 0


class ProductoUpdate(BaseModel):
    nombre: Optional[str] = None
    categoria: Optional[str] = None
    icono: Optional[str] = None
    precio: Optional[float] = None
    costo: Optional[float] = None
    stock: Optional[int] = None
    stock_min: Optional[int] = None
    vencimiento: Optional[str] = None
    descuento: Optional[float] = None
    activo: Optional[bool] = None


class ProveedorCreate(BaseModel):
    id: str
    nombre: str
    rut: str
    categoria: str
    contacto: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None
    plazo_pago: int = 30
    frecuencia: str = "Semanal"
    notas: Optional[str] = None


class ProveedorUpdate(BaseModel):
    nombre: Optional[str] = None
    rut: Optional[str] = None
    categoria: Optional[str] = None
    contacto: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None
    plazo_pago: Optional[int] = None
    frecuencia: Optional[str] = None
    notas: Optional[str] = None
    activo: Optional[bool] = None


class OrdenCreate(BaseModel):
    id: Optional[str] = None
    proveedor_id: str
    producto: str
    cantidad: int
    precio: float
    fecha: str
    estado: str = "pendiente"
    notas: Optional[str] = None


class OrdenUpdate(BaseModel):
    producto: Optional[str] = None
    cantidad: Optional[int] = None
    precio: Optional[float] = None
    fecha: Optional[str] = None
    estado: Optional[str] = None
    notas: Optional[str] = None


class VentaItem(BaseModel):
    producto_id: str
    nombre: str
    cantidad: int
    precio: float
    descuento: float = 0


class VentaCreate(BaseModel):
    total: float
    metodo_pago: str
    items: List[VentaItem]


class TurnoCreate(BaseModel):
    cajero_id: int
    fecha: Optional[str] = None
    hora_inicio: str
    hora_fin: Optional[str] = None
    estado: str = "activo"
    notas: Optional[str] = None


class TurnoUpdate(BaseModel):
    hora_fin: Optional[str] = None
    estado: Optional[str] = None
    notas: Optional[str] = None


class RestockRequest(BaseModel):
    cantidad: int
    proveedor: Optional[str] = None
    nota: Optional[str] = None


class ProfileUpdate(BaseModel):
    nombre: Optional[str] = None
    notif_email_admin: Optional[str] = None   # correo destino de alertas
    smtp_email: Optional[str] = None           # cuenta Gmail que envía
    smtp_app_password: Optional[str] = None    # App Password de Google


class TestEmailRequest(BaseModel):
    smtp_email: str
    smtp_app_password: str
    notif_email_admin: str

# ══════════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════════


@app.post("/api/auth/login")
def login(data: LoginRequest):
    with get_db() as conn:
        user = row_to_dict(conn.execute(
            "SELECT * FROM usuarios WHERE usuario=?", (data.usuario,)
        ).fetchone())
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    if not user["activo"]:
        raise HTTPException(
            status_code=403, detail="Cuenta desactivada. Contacta al administrador.")
    if user["password"] != hash_pw(data.password):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")
    token = create_token(user["id"], user["rol"])
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "nombre": user["nombre"],
            "usuario": user["usuario"],
            "rol": user["rol"],
            "activo": bool(user["activo"]),
        }
    }


@app.get("/api/auth/me")
def me(user=Depends(get_current_user)):
    return {k: v for k, v in user.items() if k != "password"}


@app.post("/api/auth/change-password")
def change_password(data: PasswordChangeRequest, user=Depends(get_current_user)):
    if user["password"] != hash_pw(data.current_password):
        raise HTTPException(
            status_code=400, detail="Contraseña actual incorrecta")
    with get_db() as conn:
        conn.execute(
            "UPDATE usuarios SET password=? WHERE id=?",
            (hash_pw(data.new_password), user["id"])
        )
    return {"message": "Contraseña actualizada"}


@app.get("/api/auth/profile")
def get_profile(user=Depends(get_current_user)):
    """Retorna datos del perfil del usuario + configuración de email (solo admin)."""
    profile = {k: v for k, v in user.items() if k != "password"}
    if user["rol"] == "admin":
        with get_db() as conn:
            profile["smtp_email"] = get_config(conn, "smtp_email")
            profile["notif_email_admin"] = get_config(
                conn, "notif_email_admin")
            # Nunca devolver la contraseña real; solo indicar si está configurada
            raw_pass = get_config(conn, "smtp_app_password")
            profile["smtp_configured"] = bool(raw_pass)
    return profile


@app.patch("/api/auth/profile")
def update_profile(data: ProfileUpdate, user=Depends(get_current_user)):
    """Actualiza nombre del usuario y (solo admin) configuración SMTP."""
    if data.nombre is not None:
        with get_db() as conn:
            conn.execute(
                "UPDATE usuarios SET nombre=? WHERE id=?",
                (data.nombre.strip(), user["id"])
            )

    if user["rol"] == "admin":
        with get_db() as conn:
            if data.smtp_email is not None:
                set_config(conn, "smtp_email", data.smtp_email.strip())
            if data.smtp_app_password is not None:
                set_config(conn, "smtp_app_password",
                           data.smtp_app_password.strip())
            if data.notif_email_admin is not None:
                set_config(conn, "notif_email_admin",
                           data.notif_email_admin.strip())
    elif any(v is not None for v in [data.smtp_email, data.smtp_app_password, data.notif_email_admin]):
        raise HTTPException(
            status_code=403,
            detail="Solo el administrador puede modificar la configuración de correo"
        )

    return {"message": "Perfil actualizado"}


@app.post("/api/auth/test-email")
def test_email(data: TestEmailRequest, user=Depends(require_admin)):
    """Envía un correo de prueba con las credenciales proporcionadas."""
    if not data.smtp_email or not data.smtp_app_password or not data.notif_email_admin:
        raise HTTPException(
            status_code=400,
            detail="Debes ingresar correo SMTP, App Password y correo destino"
        )
    subject = "✅ FreshMart — Correo de prueba"
    body = f"""
    <div style="font-family:'Segoe UI',Arial,sans-serif;max-width:500px;margin:0 auto;padding:24px">
      <div style="background:#fff;border-radius:12px;border:1px solid #e5e7eb;overflow:hidden">
        <div style="background:#16a34a;padding:20px 24px">
          <h2 style="margin:0;color:#fff;font-size:18px">🛒 FreshMart ERP</h2>
        </div>
        <div style="padding:24px">
          <p style="color:#374151;font-size:15px">
            ¡Configuración exitosa! Las notificaciones de stock bajo mínimo serán
            enviadas a <strong>{data.notif_email_admin}</strong> cada vez que un
            producto alcance su límite.
          </p>
          <p style="color:#6b7280;font-size:13px">
            Este correo fue enviado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}.
          </p>
        </div>
      </div>
    </div>
    """
    try:
        send_email(data.smtp_email, data.smtp_app_password,
                   data.notif_email_admin, subject, body)
    except smtplib.SMTPAuthenticationError:
        raise HTTPException(
            status_code=400,
            detail="Error de autenticación: verifica que el correo y App Password sean correctos"
        )
    except smtplib.SMTPException as e:
        raise HTTPException(status_code=400, detail=f"Error SMTP: {str(e)}")
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo enviar el correo: {str(e)}"
        )
    return {"message": "Correo de prueba enviado correctamente"}


@app.get("/api/notifications/stock-alerts")
def stock_alerts(user=Depends(require_supervisor)):
    """Retorna productos activos con stock <= stock_min para mostrar en el dashboard."""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT id, nombre, categoria, icono, stock, stock_min
               FROM productos
               WHERE activo=1 AND stock <= stock_min
               ORDER BY stock ASC"""
        ).fetchall()
    return {"data": rows_to_list(rows), "total": len(rows)}

# ══════════════════════════════════════════════════════════════════
# USUARIOS / CAJEROS
# ══════════════════════════════════════════════════════════════════


@app.get("/api/usuarios")
def list_usuarios(user=Depends(require_admin)):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id,nombre,usuario,rol,pin,activo,creado FROM usuarios ORDER BY id"
        ).fetchall()
    return rows_to_list(rows)


@app.post("/api/usuarios", status_code=201)
def create_usuario(data: UsuarioCreate, user=Depends(require_admin)):
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM usuarios WHERE usuario=?", (data.usuario,)).fetchone()
        if existing:
            raise HTTPException(
                status_code=400, detail="El nombre de usuario ya existe")
        conn.execute(
            "INSERT INTO usuarios (nombre,usuario,password,rol,pin,activo) VALUES (?,?,?,?,?,?)",
            (data.nombre, data.usuario, hash_pw(data.password),
             data.rol, data.pin, int(data.activo))
        )
        new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    return {"id": new_id, "message": "Usuario creado"}


@app.get("/api/usuarios/{uid}")
def get_usuario(uid: int, user=Depends(require_admin)):
    with get_db() as conn:
        row = conn.execute(
            "SELECT id,nombre,usuario,rol,pin,activo,creado FROM usuarios WHERE id=?", (
                uid,)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return row_to_dict(row)


@app.patch("/api/usuarios/{uid}")
def update_usuario(uid: int, data: UsuarioUpdate, user=Depends(require_admin)):
    updates = {}
    if data.nombre is not None:
        updates["nombre"] = data.nombre
    if data.usuario is not None:
        updates["usuario"] = data.usuario
    if data.password is not None:
        updates["password"] = hash_pw(data.password)
    if data.rol is not None:
        updates["rol"] = data.rol
    if data.pin is not None:
        updates["pin"] = data.pin
    if data.activo is not None:
        updates["activo"] = int(data.activo)
    if not updates:
        raise HTTPException(
            status_code=400, detail="No hay campos para actualizar")
    set_clause = ", ".join(f"{k}=?" for k in updates)
    with get_db() as conn:
        conn.execute(
            f"UPDATE usuarios SET {set_clause} WHERE id=?", (*updates.values(), uid))
    return {"message": "Usuario actualizado"}


@app.delete("/api/usuarios/{uid}")
def delete_usuario(uid: int, admin=Depends(require_admin)):
    if uid == admin["id"]:
        raise HTTPException(
            status_code=400, detail="No puedes eliminar tu propia cuenta")
    with get_db() as conn:
        # Verificar que el usuario existe
        if not conn.execute("SELECT id FROM usuarios WHERE id=?", (uid,)).fetchone():
            raise HTTPException(
                status_code=404, detail="Usuario no encontrado")
        # Bloquear si tiene ventas (registros contables, no se borran)
        ventas = conn.execute(
            "SELECT COUNT(*) FROM ventas WHERE cajero_id=?", (uid,)
        ).fetchone()[0]
        if ventas > 0:
            raise HTTPException(
                status_code=400,
                detail=f"No se puede eliminar: el usuario tiene {ventas} venta(s) registrada(s). Desactívalo en su lugar."
            )
        # Eliminar turnos asociados (datos operativos, sí se pueden borrar)
        conn.execute("DELETE FROM turnos WHERE cajero_id=?", (uid,))
        # Ahora sí eliminar el usuario sin violar FK
        conn.execute("DELETE FROM usuarios WHERE id=?", (uid,))
    return {"message": "Usuario eliminado"}

# ══════════════════════════════════════════════════════════════════
# PRODUCTOS / INVENTARIO
# ══════════════════════════════════════════════════════════════════


@app.get("/api/productos")
def list_productos(
    q: Optional[str] = None,
    categoria: Optional[str] = None,
    estado: Optional[str] = None,
    user=Depends(get_current_user)
):
    sql = "SELECT * FROM productos WHERE activo=1"
    params = []
    if q:
        sql += " AND (nombre LIKE ? OR id LIKE ?)"
        params += [f"%{q}%", f"%{q}%"]
    if categoria:
        sql += " AND categoria=?"
        params.append(categoria)
    sql += " ORDER BY categoria, nombre"
    with get_db() as conn:
        rows = conn.execute(sql, params).fetchall()
    productos = rows_to_list(rows)
    if estado == "critico":
        productos = [p for p in productos if p["stock"] <= 5]
    elif estado == "bajo":
        productos = [p for p in productos if 5 < p["stock"] <= p["stock_min"]]
    elif estado == "ok":
        productos = [p for p in productos if p["stock"] > p["stock_min"]]
    return productos


@app.post("/api/productos", status_code=201)
def create_producto(data: ProductoCreate, user=Depends(require_supervisor)):
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM productos WHERE id=?", (data.id,)).fetchone()
        if existing:
            raise HTTPException(
                status_code=400, detail="Ya existe un producto con ese código de barras")
        conn.execute(
            "INSERT INTO productos (id,nombre,categoria,icono,precio,costo,stock,stock_min,vencimiento,descuento) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (data.id, data.nombre, data.categoria, data.icono, data.precio, data.costo,
             data.stock, data.stock_min, data.vencimiento, data.descuento)
        )
    return {"id": data.id, "message": "Producto creado"}


@app.get("/api/productos/{pid}")
def get_producto(pid: str, user=Depends(get_current_user)):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM productos WHERE id=?", (pid,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return row_to_dict(row)


@app.patch("/api/productos/{pid}")
def update_producto(pid: str, data: ProductoUpdate, user=Depends(require_supervisor)):
    updates = {}
    if data.nombre is not None:
        updates["nombre"] = data.nombre
    if data.categoria is not None:
        updates["categoria"] = data.categoria
    if data.icono is not None:
        updates["icono"] = data.icono
    if data.precio is not None:
        updates["precio"] = data.precio
    if data.costo is not None:
        updates["costo"] = data.costo
    if data.stock is not None:
        updates["stock"] = data.stock
    if data.stock_min is not None:
        updates["stock_min"] = data.stock_min
    if data.vencimiento is not None:
        updates["vencimiento"] = data.vencimiento
    if data.descuento is not None:
        updates["descuento"] = data.descuento
    if data.activo is not None:
        updates["activo"] = int(data.activo)
    if not updates:
        raise HTTPException(
            status_code=400, detail="No hay campos para actualizar")
    set_clause = ", ".join(f"{k}=?" for k in updates)
    with get_db() as conn:
        conn.execute(
            f"UPDATE productos SET {set_clause} WHERE id=?", (*updates.values(), pid))
    return {"message": "Producto actualizado"}


@app.delete("/api/productos/{pid}")
def delete_producto(pid: str, user=Depends(require_supervisor)):
    with get_db() as conn:
        conn.execute("UPDATE productos SET activo=0 WHERE id=?", (pid,))
    return {"message": "Producto eliminado"}


@app.post("/api/productos/{pid}/restock")
def restock_producto(pid: str, data: RestockRequest, user=Depends(require_supervisor)):
    if data.cantidad <= 0:
        raise HTTPException(
            status_code=400, detail="La cantidad debe ser mayor a 0")
    with get_db() as conn:
        prod = conn.execute(
            "SELECT stock FROM productos WHERE id=? AND activo=1", (pid,)).fetchone()
        if not prod:
            raise HTTPException(
                status_code=404, detail="Producto no encontrado")
        new_stock = prod["stock"] + data.cantidad
        conn.execute("UPDATE productos SET stock=? WHERE id=?",
                     (new_stock, pid))
        conn.execute(
            "INSERT INTO reposiciones (producto_id,cantidad,proveedor,nota) VALUES (?,?,?,?)",
            (pid, data.cantidad, data.proveedor, data.nota)
        )
    return {"message": "Stock actualizado", "nuevo_stock": new_stock}


@app.get("/api/categorias")
def list_categorias(user=Depends(get_current_user)):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT DISTINCT categoria FROM productos WHERE activo=1 ORDER BY categoria").fetchall()
    return [r["categoria"] for r in rows]

# ══════════════════════════════════════════════════════════════════
# PROVEEDORES
# ══════════════════════════════════════════════════════════════════


@app.get("/api/proveedores")
def list_proveedores(q: Optional[str] = None, user=Depends(require_supervisor)):
    sql = "SELECT * FROM proveedores WHERE activo=1"
    params = []
    if q:
        sql += " AND (nombre LIKE ? OR rut LIKE ?)"
        params += [f"%{q}%", f"%{q}%"]
    sql += " ORDER BY nombre"
    with get_db() as conn:
        rows = conn.execute(sql, params).fetchall()
    return rows_to_list(rows)


@app.post("/api/proveedores", status_code=201)
def create_proveedor(data: ProveedorCreate, user=Depends(require_supervisor)):
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM proveedores WHERE id=?", (data.id,)).fetchone()
        if existing:
            raise HTTPException(
                status_code=400, detail="Ya existe un proveedor con ese ID")
        conn.execute(
            "INSERT INTO proveedores (id,nombre,rut,categoria,contacto,telefono,email,direccion,plazo_pago,frecuencia,notas) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (data.id, data.nombre, data.rut, data.categoria, data.contacto, data.telefono,
             data.email, data.direccion, data.plazo_pago, data.frecuencia, data.notas)
        )
    return {"id": data.id, "message": "Proveedor creado"}


@app.get("/api/proveedores/{pid}")
def get_proveedor(pid: str, user=Depends(require_supervisor)):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM proveedores WHERE id=?", (pid,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return row_to_dict(row)


@app.patch("/api/proveedores/{pid}")
def update_proveedor(pid: str, data: ProveedorUpdate, user=Depends(require_supervisor)):
    updates = {}
    if data.nombre is not None:
        updates["nombre"] = data.nombre
    if data.rut is not None:
        updates["rut"] = data.rut
    if data.categoria is not None:
        updates["categoria"] = data.categoria
    if data.contacto is not None:
        updates["contacto"] = data.contacto
    if data.telefono is not None:
        updates["telefono"] = data.telefono
    if data.email is not None:
        updates["email"] = data.email
    if data.direccion is not None:
        updates["direccion"] = data.direccion
    if data.plazo_pago is not None:
        updates["plazo_pago"] = data.plazo_pago
    if data.frecuencia is not None:
        updates["frecuencia"] = data.frecuencia
    if data.notas is not None:
        updates["notas"] = data.notas
    if data.activo is not None:
        updates["activo"] = int(data.activo)
    if not updates:
        raise HTTPException(
            status_code=400, detail="No hay campos para actualizar")
    set_clause = ", ".join(f"{k}=?" for k in updates)
    with get_db() as conn:
        conn.execute(
            f"UPDATE proveedores SET {set_clause} WHERE id=?", (*updates.values(), pid))
    return {"message": "Proveedor actualizado"}


@app.delete("/api/proveedores/{pid}")
def delete_proveedor(pid: str, user=Depends(require_supervisor)):
    with get_db() as conn:
        conn.execute("UPDATE proveedores SET activo=0 WHERE id=?", (pid,))
    return {"message": "Proveedor eliminado"}

# ══════════════════════════════════════════════════════════════════
# ÓRDENES
# ══════════════════════════════════════════════════════════════════


@app.get("/api/ordenes")
def list_ordenes(proveedor_id: Optional[str] = None, user=Depends(require_supervisor)):
    sql = "SELECT o.*, p.nombre as proveedor_nombre FROM ordenes o JOIN proveedores p ON o.proveedor_id=p.id"
    params = []
    if proveedor_id:
        sql += " WHERE o.proveedor_id=?"
        params.append(proveedor_id)
    sql += " ORDER BY o.fecha DESC"
    with get_db() as conn:
        rows = conn.execute(sql, params).fetchall()
    return rows_to_list(rows)


@app.post("/api/ordenes", status_code=201)
def create_orden(data: OrdenCreate, user=Depends(require_supervisor)):
    with get_db() as conn:
        # Generar ID automático si no se provee
        if not data.id:
            count = conn.execute("SELECT COUNT(*) FROM ordenes").fetchone()[0]
            orden_id = f"OC-{str(count+1).zfill(3)}"
        else:
            orden_id = data.id
        conn.execute(
            "INSERT INTO ordenes (id,proveedor_id,producto,cantidad,precio,fecha,estado,notas) VALUES (?,?,?,?,?,?,?,?)",
            (orden_id, data.proveedor_id, data.producto, data.cantidad, data.precio,
             data.fecha, data.estado, data.notas)
        )
    return {"id": orden_id, "message": "Orden creada"}


@app.patch("/api/ordenes/{oid}")
def update_orden(oid: str, data: OrdenUpdate, user=Depends(require_supervisor)):
    updates = {}
    if data.producto is not None:
        updates["producto"] = data.producto
    if data.cantidad is not None:
        updates["cantidad"] = data.cantidad
    if data.precio is not None:
        updates["precio"] = data.precio
    if data.fecha is not None:
        updates["fecha"] = data.fecha
    if data.estado is not None:
        updates["estado"] = data.estado
    if data.notas is not None:
        updates["notas"] = data.notas
    if not updates:
        raise HTTPException(
            status_code=400, detail="No hay campos para actualizar")
    set_clause = ", ".join(f"{k}=?" for k in updates)
    with get_db() as conn:
        conn.execute(
            f"UPDATE ordenes SET {set_clause} WHERE id=?", (*updates.values(), oid))
    return {"message": "Orden actualizada"}


@app.delete("/api/ordenes/{oid}")
def delete_orden(oid: str, user=Depends(require_supervisor)):
    with get_db() as conn:
        conn.execute("DELETE FROM ordenes WHERE id=?", (oid,))
    return {"message": "Orden eliminada"}

# ══════════════════════════════════════════════════════════════════
# VENTAS
# ══════════════════════════════════════════════════════════════════


@app.get("/api/ventas")
def list_ventas(fecha: Optional[str] = None, user=Depends(require_supervisor)):
    sql = """
    SELECT v.*, u.nombre as cajero_nombre
    FROM ventas v JOIN usuarios u ON v.cajero_id=u.id
    """
    params = []
    if fecha:
        sql += " WHERE date(v.creado)=?"
        params.append(fecha)
    else:
        sql += " WHERE date(v.creado)=date('now')"
    sql += " ORDER BY v.creado DESC"
    with get_db() as conn:
        rows = conn.execute(sql, params).fetchall()
    return rows_to_list(rows)


@app.post("/api/ventas", status_code=201)
def create_venta(data: VentaCreate, user=Depends(get_current_user)):
    with get_db() as conn:
        # Verificar stock de todos los items primero
        for item in data.items:
            prod = conn.execute(
                "SELECT stock, nombre FROM productos WHERE id=? AND activo=1", (
                    item.producto_id,)
            ).fetchone()
            if not prod:
                raise HTTPException(
                    status_code=404, detail=f"Producto {item.producto_id} no encontrado")
            if prod["stock"] < item.cantidad:
                raise HTTPException(
                    status_code=400,
                    detail=f"Stock insuficiente para '{prod['nombre']}'. Disponible: {prod['stock']}"
                )
        # Insertar venta
        conn.execute(
            "INSERT INTO ventas (cajero_id, total, metodo_pago) VALUES (?,?,?)",
            (user["id"], data.total, data.metodo_pago)
        )
        venta_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        # Insertar detalles y actualizar stock
        for item in data.items:
            conn.execute(
                "INSERT INTO detalle_ventas (venta_id,producto_id,nombre,cantidad,precio,descuento) VALUES (?,?,?,?,?,?)",
                (venta_id, item.producto_id, item.nombre,
                 item.cantidad, item.precio, item.descuento)
            )
            conn.execute(
                "UPDATE productos SET stock = stock - ? WHERE id=?",
                (item.cantidad, item.producto_id)
            )
    # Notificar stock bajo en background (no bloquea la respuesta)
    _check_and_notify_stock([item.producto_id for item in data.items])
    return {"id": venta_id, "message": "Venta procesada"}


@app.get("/api/ventas/{vid}/detalle")
def get_venta_detalle(vid: int, user=Depends(get_current_user)):
    with get_db() as conn:
        venta = row_to_dict(conn.execute(
            "SELECT * FROM ventas WHERE id=?", (vid,)).fetchone())
        if not venta:
            raise HTTPException(status_code=404, detail="Venta no encontrada")
        items = rows_to_list(conn.execute(
            "SELECT * FROM detalle_ventas WHERE venta_id=?", (vid,)
        ).fetchall())
    return {**venta, "items": items}

# ══════════════════════════════════════════════════════════════════
# TURNOS
# ══════════════════════════════════════════════════════════════════


@app.get("/api/turnos")
def list_turnos(fecha: Optional[str] = None, cajero_id: Optional[int] = None, user=Depends(require_supervisor)):
    sql = """
    SELECT t.*, u.nombre as cajero_nombre, u.rol as cajero_rol
    FROM turnos t JOIN usuarios u ON t.cajero_id=u.id
    WHERE 1=1
    """
    params = []
    if fecha:
        sql += " AND t.fecha=?"
        params.append(fecha)
    else:
        sql += " AND t.fecha=date('now')"
    if cajero_id:
        sql += " AND t.cajero_id=?"
        params.append(cajero_id)
    sql += " ORDER BY t.hora_inicio"
    with get_db() as conn:
        rows = conn.execute(sql, params).fetchall()
    return rows_to_list(rows)


@app.post("/api/turnos", status_code=201)
def create_turno(data: TurnoCreate, user=Depends(require_supervisor)):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO turnos (cajero_id,fecha,hora_inicio,hora_fin,estado,notas) VALUES (?,?,?,?,?,?)",
            (data.cajero_id, data.fecha or date.today().isoformat(),
             data.hora_inicio, data.hora_fin, data.estado, data.notas)
        )
        new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    return {"id": new_id, "message": "Turno creado"}


@app.patch("/api/turnos/{tid}")
def update_turno(tid: int, data: TurnoUpdate, user=Depends(require_supervisor)):
    updates = {}
    if data.hora_fin is not None:
        updates["hora_fin"] = data.hora_fin
    if data.estado is not None:
        updates["estado"] = data.estado
    if data.notas is not None:
        updates["notas"] = data.notas
    if not updates:
        raise HTTPException(
            status_code=400, detail="No hay campos para actualizar")
    set_clause = ", ".join(f"{k}=?" for k in updates)
    with get_db() as conn:
        conn.execute(
            f"UPDATE turnos SET {set_clause} WHERE id=?", (*updates.values(), tid))
    return {"message": "Turno actualizado"}


@app.delete("/api/turnos/{tid}")
def delete_turno(tid: int, user=Depends(require_supervisor)):
    with get_db() as conn:
        conn.execute("DELETE FROM turnos WHERE id=?", (tid,))
    return {"message": "Turno eliminado"}

# ══════════════════════════════════════════════════════════════════
# HISTORIAL DE VENTAS
# ══════════════════════════════════════════════════════════════════


@app.get("/api/sales/history")
def sales_history(
    period: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
    user=Depends(require_supervisor)
):
    """
    Retorna historial de ventas con filtros opcionales.
    - period: 'today' | 'week' | 'month'
    - start_date / end_date: rango personalizado YYYY-MM-DD
    - page / per_page: paginación
    """
    # Validaciones
    if page < 1:
        raise HTTPException(status_code=400, detail="page debe ser >= 1")
    if per_page < 1 or per_page > 200:
        raise HTTPException(
            status_code=400, detail="per_page debe estar entre 1 y 200")
    if period and period not in ("today", "week", "month"):
        raise HTTPException(
            status_code=400, detail="period debe ser 'today', 'week' o 'month'")
    if start_date:
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400, detail="start_date debe tener formato YYYY-MM-DD")
    if end_date:
        try:
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400, detail="end_date debe tener formato YYYY-MM-DD")

    # Construir filtro de fecha
    date_filter = ""
    params: list = []

    if period == "today":
        date_filter = " AND date(v.creado) = date('now')"
    elif period == "week":
        date_filter = " AND date(v.creado) >= date('now', '-6 days')"
    elif period == "month":
        date_filter = " AND date(v.creado) >= date('now', 'start of month')"
    elif start_date and end_date:
        date_filter = " AND date(v.creado) BETWEEN ? AND ?"
        params += [start_date, end_date]
    elif start_date:
        date_filter = " AND date(v.creado) >= ?"
        params.append(start_date)
    elif end_date:
        date_filter = " AND date(v.creado) <= ?"
        params.append(end_date)

    base_sql = f"""
        FROM ventas v
        JOIN usuarios u ON v.cajero_id = u.id
        WHERE 1=1{date_filter}
    """

    with get_db() as conn:
        # Total de registros para paginación
        total_count = conn.execute(
            f"SELECT COUNT(*) {base_sql}", params
        ).fetchone()[0]

        offset = (page - 1) * per_page
        rows = conn.execute(
            f"""
            SELECT
                v.id,
                v.total,
                v.metodo_pago,
                v.creado,
                v.cajero_id,
                u.nombre  AS cajero_nombre,
                (SELECT COUNT(*) FROM detalle_ventas dv WHERE dv.venta_id = v.id) AS num_productos
            {base_sql}
            ORDER BY v.creado DESC
            LIMIT ? OFFSET ?
            """,
            params + [per_page, offset]
        ).fetchall()

    ventas = rows_to_list(rows)

    return {
        "success": True,
        "data": ventas,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total_count,
            "pages": max(1, -(-total_count // per_page))  # ceil division
        }
    }


@app.get("/api/sales/summary")
def sales_summary(
    period: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user=Depends(require_supervisor)
):
    """
    Retorna resumen: total_vendido, cantidad_ventas, ticket_promedio.
    Acepta los mismos filtros que /api/sales/history.
    """
    if period and period not in ("today", "week", "month"):
        raise HTTPException(
            status_code=400, detail="period debe ser 'today', 'week' o 'month'")

    date_filter = ""
    params: list = []

    if period == "today":
        date_filter = " AND date(creado) = date('now')"
    elif period == "week":
        date_filter = " AND date(creado) >= date('now', '-6 days')"
    elif period == "month":
        date_filter = " AND date(creado) >= date('now', 'start of month')"
    elif start_date and end_date:
        date_filter = " AND date(creado) BETWEEN ? AND ?"
        params += [start_date, end_date]
    elif start_date:
        date_filter = " AND date(creado) >= ?"
        params.append(start_date)
    elif end_date:
        date_filter = " AND date(creado) <= ?"
        params.append(end_date)

    with get_db() as conn:
        row = conn.execute(
            f"""
            SELECT
                COALESCE(SUM(total), 0)   AS total_vendido,
                COUNT(*)                  AS cantidad_ventas,
                COALESCE(AVG(total), 0)   AS ticket_promedio
            FROM ventas
            WHERE 1=1{date_filter}
            """,
            params
        ).fetchone()

    return {
        "success": True,
        "data": {
            "total_vendido": row["total_vendido"],
            "cantidad_ventas": row["cantidad_ventas"],
            "ticket_promedio": round(row["ticket_promedio"], 0)
        }
    }


# ══════════════════════════════════════════════════════════════════
# DASHBOARD / ESTADÍSTICAS
# ══════════════════════════════════════════════════════════════════


@app.get("/api/dashboard")
def dashboard(user=Depends(get_current_user)):
    with get_db() as conn:
        ventas_hoy = conn.execute("""
            SELECT COALESCE(SUM(total),0) as total, COUNT(*) as count
            FROM ventas WHERE date(creado)=date('now')
        """).fetchone()
        total_productos = conn.execute(
            "SELECT COUNT(*) FROM productos WHERE activo=1").fetchone()[0]
        criticos = conn.execute(
            "SELECT COUNT(*) FROM productos WHERE activo=1 AND stock<=5"
        ).fetchone()[0]
        bajos = conn.execute(
            "SELECT COUNT(*) FROM productos WHERE activo=1 AND stock>5 AND stock<=stock_min"
        ).fetchone()[0]
        ord_pendientes = conn.execute(
            "SELECT COUNT(*) FROM ordenes WHERE estado='pendiente'"
        ).fetchone()[0]
        # Últimas ventas de hoy
        ultimas_ventas = rows_to_list(conn.execute("""
            SELECT v.*, u.nombre as cajero_nombre
            FROM ventas v JOIN usuarios u ON v.cajero_id=u.id
            WHERE date(v.creado)=date('now')
            ORDER BY v.creado DESC LIMIT 10
        """).fetchall())
        # Top productos (por unidades vendidas hoy)
        top_prods = rows_to_list(conn.execute("""
            SELECT d.nombre, SUM(d.cantidad) as total_vendidos
            FROM detalle_ventas d JOIN ventas v ON d.venta_id=v.id
            WHERE date(v.creado)=date('now')
            GROUP BY d.producto_id ORDER BY total_vendidos DESC LIMIT 5
        """).fetchall())
    return {
        "ventas_hoy_total": ventas_hoy["total"],
        "ventas_hoy_count": ventas_hoy["count"],
        "total_productos": total_productos,
        "criticos": criticos,
        "bajos": bajos,
        "ordenes_pendientes": ord_pendientes,
        "ultimas_ventas": ultimas_ventas,
        "top_productos": top_prods,
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "1.0.0"}
