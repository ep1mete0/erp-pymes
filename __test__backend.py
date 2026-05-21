"""
FreshMart — Suite de Tests Backend
Cubre: Auth, Usuarios, Productos, Proveedores, Órdenes, Ventas, Turnos, Dashboard
Ejecutar: pytest test_backend.py -v
"""

import pytest
import sqlite3
import os
import sys

# ── Apuntar al directorio donde está main.py ──────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from fastapi.testclient import TestClient

# Usar una BD en memoria para tests (no contamina la BD real)
TEST_DB = "test_freshmart.db"
os.environ["FRESHMART_SECRET"] = "test-secret-key"

# Patch DB_PATH antes de importar main
import main as app_module
app_module.DB_PATH = TEST_DB

from main import app, hash_pw

client = TestClient(app)

# ══════════════════════════════════════════════════════════════════
#  FIXTURES
# ══════════════════════════════════════════════════════════════════

def init_test_db():
    """Crea el esquema y datos iniciales para tests."""
    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        PRAGMA foreign_keys = ON;

        DROP TABLE IF EXISTS detalle_ventas;
        DROP TABLE IF EXISTS ventas;
        DROP TABLE IF EXISTS reposiciones;
        DROP TABLE IF EXISTS turnos;
        DROP TABLE IF EXISTS ordenes;
        DROP TABLE IF EXISTS proveedores;
        DROP TABLE IF EXISTS productos;
        DROP TABLE IF EXISTS usuarios;

        CREATE TABLE usuarios (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre   TEXT NOT NULL,
            usuario  TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol      TEXT NOT NULL DEFAULT 'cajero',
            pin      TEXT DEFAULT '0000',
            activo   INTEGER DEFAULT 1,
            creado   TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE productos (
            id          TEXT PRIMARY KEY,
            nombre      TEXT NOT NULL,
            categoria   TEXT NOT NULL,
            icono       TEXT DEFAULT '📦',
            precio      REAL DEFAULT 0,
            costo       REAL DEFAULT 0,
            stock       INTEGER DEFAULT 0,
            stock_min   INTEGER DEFAULT 5,
            vencimiento TEXT,
            descuento   REAL DEFAULT 0,
            activo      INTEGER DEFAULT 1
        );

        CREATE TABLE proveedores (
            id          TEXT PRIMARY KEY,
            nombre      TEXT NOT NULL,
            rut         TEXT,
            categoria   TEXT,
            contacto    TEXT,
            telefono    TEXT,
            email       TEXT,
            direccion   TEXT,
            plazo_pago  INTEGER DEFAULT 30,
            frecuencia  TEXT DEFAULT 'Semanal',
            notas       TEXT,
            activo      INTEGER DEFAULT 1
        );

        CREATE TABLE ordenes (
            id           TEXT PRIMARY KEY,
            proveedor_id TEXT NOT NULL,
            producto     TEXT NOT NULL,
            cantidad     INTEGER NOT NULL,
            precio       REAL NOT NULL,
            fecha        TEXT NOT NULL,
            estado       TEXT DEFAULT 'pendiente',
            notas        TEXT,
            creado       TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (proveedor_id) REFERENCES proveedores(id)
        );

        CREATE TABLE ventas (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            cajero_id   INTEGER NOT NULL,
            total       REAL NOT NULL,
            metodo_pago TEXT NOT NULL,
            creado      TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (cajero_id) REFERENCES usuarios(id)
        );

        CREATE TABLE detalle_ventas (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id    INTEGER NOT NULL,
            producto_id TEXT NOT NULL,
            nombre      TEXT NOT NULL,
            cantidad    INTEGER NOT NULL,
            precio      REAL NOT NULL,
            descuento   REAL DEFAULT 0,
            FOREIGN KEY (venta_id) REFERENCES ventas(id)
        );

        CREATE TABLE turnos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            cajero_id   INTEGER NOT NULL,
            fecha       TEXT NOT NULL,
            hora_inicio TEXT NOT NULL,
            hora_fin    TEXT,
            estado      TEXT DEFAULT 'activo',
            notas       TEXT,
            FOREIGN KEY (cajero_id) REFERENCES usuarios(id)
        );

        CREATE TABLE reposiciones (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id TEXT NOT NULL,
            cantidad    INTEGER NOT NULL,
            proveedor   TEXT,
            nota        TEXT,
            creado      TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS config (
            clave TEXT PRIMARY KEY,
            valor TEXT NOT NULL DEFAULT ''
        );
    """)

    # Seed: usuarios
    conn.execute("INSERT INTO usuarios (nombre,usuario,password,rol,pin,activo) VALUES (?,?,?,?,?,?)",
                 ("Admin Test", "admin", hash_pw("admin123"), "admin", "1234", 1))
    conn.execute("INSERT INTO usuarios (nombre,usuario,password,rol,pin,activo) VALUES (?,?,?,?,?,?)",
                 ("Supervisor Test", "vsoto", hash_pw("super456"), "supervisor", "5678", 1))
    conn.execute("INSERT INTO usuarios (nombre,usuario,password,rol,pin,activo) VALUES (?,?,?,?,?,?)",
                 ("Cajero Test", "rfuentes", hash_pw("caja789"), "cajero", "9012", 1))
    conn.execute("INSERT INTO usuarios (nombre,usuario,password,rol,pin,activo) VALUES (?,?,?,?,?,?)",
                 ("Inactivo Test", "inactivo", hash_pw("pass"), "cajero", "0000", 0))

    # Seed: productos
    conn.execute("INSERT INTO productos VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                 ("PROD001", "Leche Entera", "Lácteos", "🥛", 1500, 900, 50, 10, "2025-12-31", 0, 1))
    conn.execute("INSERT INTO productos VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                 ("PROD002", "Pan Marraqueta", "Panadería", "🍞", 200, 100, 200, 30, None, 0, 1))
    conn.execute("INSERT INTO productos VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                 ("PROD003", "Stock Crítico", "Abarrotes", "📦", 500, 300, 3, 10, None, 0, 1))
    conn.execute("INSERT INTO productos VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                 ("PROD004", "Producto Inactivo", "Bebidas", "🧃", 1000, 600, 20, 5, None, 0, 0))

    # Seed: proveedor
    conn.execute("INSERT INTO proveedores VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                 ("P001", "Lácteos del Sur", "76.123.456-7", "Lácteos",
                  "Juan", "+56912345678", "juan@lacteos.cl",
                  "Av. Principal 1", 30, "Semanal", "Proveedor test", 1))

    conn.commit()
    conn.close()


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Setup BD de test al inicio de la sesión."""
    init_test_db()
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def get_token(usuario="admin", password="admin123"):
    """Helper: obtiene token JWT para un usuario."""
    r = client.post("/api/auth/login", json={"usuario": usuario, "password": password})
    assert r.status_code == 200, f"Login fallido para {usuario}: {r.text}"
    return r.json()["token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


# ══════════════════════════════════════════════════════════════════
#  HEALTH
# ══════════════════════════════════════════════════════════════════

class TestHealth:
    def test_health_ok(self):
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_health_version(self):
        r = client.get("/api/health")
        assert "version" in r.json()


# ══════════════════════════════════════════════════════════════════
#  AUTH
# ══════════════════════════════════════════════════════════════════

class TestAuth:
    def test_login_admin_ok(self):
        r = client.post("/api/auth/login", json={"usuario": "admin", "password": "admin123"})
        assert r.status_code == 200
        data = r.json()
        assert "token" in data
        assert data["user"]["rol"] == "admin"
        assert data["user"]["usuario"] == "admin"

    def test_login_supervisor_ok(self):
        r = client.post("/api/auth/login", json={"usuario": "vsoto", "password": "super456"})
        assert r.status_code == 200
        assert r.json()["user"]["rol"] == "supervisor"

    def test_login_cajero_ok(self):
        r = client.post("/api/auth/login", json={"usuario": "rfuentes", "password": "caja789"})
        assert r.status_code == 200
        assert r.json()["user"]["rol"] == "cajero"

    def test_login_wrong_password(self):
        r = client.post("/api/auth/login", json={"usuario": "admin", "password": "wrong"})
        assert r.status_code == 401

    def test_login_nonexistent_user(self):
        r = client.post("/api/auth/login", json={"usuario": "noexiste", "password": "abc"})
        assert r.status_code == 401

    def test_login_inactive_user(self):
        r = client.post("/api/auth/login", json={"usuario": "inactivo", "password": "pass"})
        assert r.status_code == 403

    def test_me_endpoint(self):
        token = get_token()
        r = client.get("/api/auth/me", headers=auth(token))
        assert r.status_code == 200
        data = r.json()
        assert data["usuario"] == "admin"
        assert "password" not in data

    def test_me_without_token(self):
        r = client.get("/api/auth/me")
        assert r.status_code in (401, 403)  # FastAPI devuelve 401 sin token

    def test_me_invalid_token(self):
        r = client.get("/api/auth/me", headers={"Authorization": "Bearer token_invalido"})
        assert r.status_code == 401

    def test_change_password(self):
        token = get_token("cajero_temp_user", "temppass") if False else None
        # Usar admin para cambiar y restaurar
        token = get_token()
        r = client.post("/api/auth/change-password",
                        headers=auth(token),
                        json={"current_password": "admin123", "new_password": "admin123"})
        # Restaurar (misma contraseña en este caso)
        assert r.status_code == 200

    def test_change_password_wrong_current(self):
        token = get_token()
        r = client.post("/api/auth/change-password",
                        headers=auth(token),
                        json={"current_password": "INCORRECTA", "new_password": "nueva"})
        assert r.status_code == 400


# ══════════════════════════════════════════════════════════════════
#  USUARIOS
# ══════════════════════════════════════════════════════════════════

class TestUsuarios:
    def test_list_usuarios_as_admin(self):
        token = get_token()
        r = client.get("/api/usuarios", headers=auth(token))
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) >= 3

    def test_list_usuarios_forbidden_for_cajero(self):
        token = get_token("rfuentes", "caja789")
        r = client.get("/api/usuarios", headers=auth(token))
        assert r.status_code == 403

    def test_list_usuarios_forbidden_for_supervisor(self):
        token = get_token("vsoto", "super456")
        r = client.get("/api/usuarios", headers=auth(token))
        assert r.status_code == 403

    def test_create_usuario(self):
        token = get_token()
        r = client.post("/api/usuarios", headers=auth(token), json={
            "nombre": "Nuevo Cajero",
            "usuario": "ncajero_test",
            "password": "pass123",
            "rol": "cajero",
            "pin": "1111"
        })
        assert r.status_code == 201
        assert "id" in r.json()

    def test_create_usuario_duplicate(self):
        token = get_token()
        payload = {"nombre": "Dup", "usuario": "admin", "password": "x", "rol": "cajero"}
        r = client.post("/api/usuarios", headers=auth(token), json=payload)
        assert r.status_code == 400

    def test_get_usuario(self):
        token = get_token()
        r = client.get("/api/usuarios/1", headers=auth(token))
        assert r.status_code == 200
        assert r.json()["usuario"] == "admin"

    def test_get_usuario_not_found(self):
        token = get_token()
        r = client.get("/api/usuarios/9999", headers=auth(token))
        assert r.status_code == 404

    def test_update_usuario(self):
        token = get_token()
        r = client.patch("/api/usuarios/3", headers=auth(token), json={"pin": "4321"})
        assert r.status_code == 200

    def test_update_usuario_no_fields(self):
        token = get_token()
        r = client.patch("/api/usuarios/1", headers=auth(token), json={})
        assert r.status_code == 400

    def test_delete_usuario(self):
        # Crear uno para eliminar
        token = get_token()
        cr = client.post("/api/usuarios", headers=auth(token), json={
            "nombre": "Para Borrar",
            "usuario": "tobedeleted",
            "password": "123",
            "rol": "cajero"
        })
        uid = cr.json()["id"]
        r = client.delete(f"/api/usuarios/{uid}", headers=auth(token))
        assert r.status_code == 200

    def test_delete_self_forbidden(self):
        token = get_token()
        r = client.delete("/api/usuarios/1", headers=auth(token))
        assert r.status_code == 400


# ══════════════════════════════════════════════════════════════════
#  PRODUCTOS
# ══════════════════════════════════════════════════════════════════

class TestProductos:
    def test_list_productos(self):
        token = get_token()
        r = client.get("/api/productos", headers=auth(token))
        assert r.status_code == 200
        items = r.json()
        assert len(items) >= 3
        # Solo activos
        assert all(p["activo"] == 1 for p in items)

    def test_list_productos_by_categoria(self):
        token = get_token()
        r = client.get("/api/productos?categoria=Lácteos", headers=auth(token))
        assert r.status_code == 200
        assert all(p["categoria"] == "Lácteos" for p in r.json())

    def test_list_productos_busqueda(self):
        token = get_token()
        r = client.get("/api/productos?q=Leche", headers=auth(token))
        assert r.status_code == 200
        assert any("Leche" in p["nombre"] for p in r.json())

    def test_list_productos_estado_critico(self):
        token = get_token()
        r = client.get("/api/productos?estado=critico", headers=auth(token))
        assert r.status_code == 200
        assert all(p["stock"] <= 5 for p in r.json())

    def test_list_productos_inactivos_excluidos(self):
        token = get_token()
        r = client.get("/api/productos", headers=auth(token))
        ids = [p["id"] for p in r.json()]
        assert "PROD004" not in ids  # producto inactivo

    def test_get_producto(self):
        token = get_token()
        r = client.get("/api/productos/PROD001", headers=auth(token))
        assert r.status_code == 200
        assert r.json()["nombre"] == "Leche Entera"

    def test_get_producto_not_found(self):
        token = get_token()
        r = client.get("/api/productos/NOEXISTE", headers=auth(token))
        assert r.status_code == 404

    def test_create_producto_supervisor(self):
        token = get_token("vsoto", "super456")
        r = client.post("/api/productos", headers=auth(token), json={
            "id": "PROD_NEW",
            "nombre": "Producto Nuevo",
            "categoria": "Bebidas",
            "precio": 1200,
            "costo": 700,
            "stock": 30,
            "stock_min": 5
        })
        assert r.status_code == 201

    def test_create_producto_duplicate_id(self):
        token = get_token()
        r = client.post("/api/productos", headers=auth(token), json={
            "id": "PROD001",
            "nombre": "Duplicado",
            "categoria": "Lácteos",
            "precio": 100,
            "costo": 50,
            "stock": 10,
            "stock_min": 2
        })
        assert r.status_code == 400

    def test_create_producto_forbidden_for_cajero(self):
        token = get_token("rfuentes", "caja789")
        r = client.post("/api/productos", headers=auth(token), json={
            "id": "PROD_X",
            "nombre": "x",
            "categoria": "x",
            "precio": 1,
            "costo": 1,
            "stock": 1,
            "stock_min": 1
        })
        assert r.status_code == 403

    def test_update_producto(self):
        token = get_token()
        r = client.patch("/api/productos/PROD002", headers=auth(token), json={"precio": 250})
        assert r.status_code == 200
        # Verificar que se actualizó
        r2 = client.get("/api/productos/PROD002", headers=auth(token))
        assert r2.json()["precio"] == 250

    def test_update_producto_no_fields(self):
        token = get_token()
        r = client.patch("/api/productos/PROD001", headers=auth(token), json={})
        assert r.status_code == 400

    def test_delete_producto_soft(self):
        token = get_token()
        # Crear uno para eliminar
        client.post("/api/productos", headers=auth(token), json={
            "id": "PROD_DEL",
            "nombre": "Para borrar",
            "categoria": "Abarrotes",
            "precio": 100,
            "costo": 50,
            "stock": 10,
            "stock_min": 2
        })
        r = client.delete("/api/productos/PROD_DEL", headers=auth(token))
        assert r.status_code == 200
        # Verificar soft delete: no aparece en listado activos
        rlist = client.get("/api/productos", headers=auth(token))
        assert "PROD_DEL" not in [p["id"] for p in rlist.json()]

    def test_restock_producto(self):
        token = get_token("vsoto", "super456")
        r = client.post("/api/productos/PROD001/restock", headers=auth(token),
                        json={"cantidad": 20, "proveedor": "P001", "nota": "Reposición test"})
        assert r.status_code == 200
        assert r.json()["nuevo_stock"] > 0

    def test_restock_cantidad_invalida(self):
        token = get_token()
        r = client.post("/api/productos/PROD001/restock", headers=auth(token),
                        json={"cantidad": 0})
        assert r.status_code == 400

    def test_restock_producto_inexistente(self):
        token = get_token()
        r = client.post("/api/productos/NOEXISTE/restock", headers=auth(token),
                        json={"cantidad": 5})
        assert r.status_code == 404

    def test_list_categorias(self):
        token = get_token()
        r = client.get("/api/categorias", headers=auth(token))
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert "Lácteos" in r.json()


# ══════════════════════════════════════════════════════════════════
#  PROVEEDORES
# ══════════════════════════════════════════════════════════════════

class TestProveedores:
    def test_list_proveedores(self):
        token = get_token("vsoto", "super456")
        r = client.get("/api/proveedores", headers=auth(token))
        assert r.status_code == 200
        assert len(r.json()) >= 1

    def test_list_proveedores_forbidden_cajero(self):
        token = get_token("rfuentes", "caja789")
        r = client.get("/api/proveedores", headers=auth(token))
        assert r.status_code == 403

    def test_list_proveedores_busqueda(self):
        token = get_token()
        r = client.get("/api/proveedores?q=Lácteos", headers=auth(token))
        assert r.status_code == 200

    def test_get_proveedor(self):
        token = get_token()
        r = client.get("/api/proveedores/P001", headers=auth(token))
        assert r.status_code == 200
        assert r.json()["nombre"] == "Lácteos del Sur"

    def test_get_proveedor_not_found(self):
        token = get_token()
        r = client.get("/api/proveedores/NOEXISTE", headers=auth(token))
        assert r.status_code == 404

    def test_create_proveedor(self):
        token = get_token()
        r = client.post("/api/proveedores", headers=auth(token), json={
            "id": "P_NEW",
            "nombre": "Proveedor Nuevo",
            "rut": "77.000.000-1",
            "categoria": "Bebidas"
        })
        assert r.status_code == 201

    def test_create_proveedor_duplicate(self):
        token = get_token()
        r = client.post("/api/proveedores", headers=auth(token), json={
            "id": "P001",
            "nombre": "Duplicado",
            "rut": "99.999.999-9",
            "categoria": "Lácteos"
        })
        assert r.status_code == 400

    def test_update_proveedor(self):
        token = get_token()
        r = client.patch("/api/proveedores/P001", headers=auth(token),
                         json={"telefono": "+56999999999"})
        assert r.status_code == 200

    def test_update_proveedor_no_fields(self):
        token = get_token()
        r = client.patch("/api/proveedores/P001", headers=auth(token), json={})
        assert r.status_code == 400

    def test_delete_proveedor_soft(self):
        token = get_token()
        client.post("/api/proveedores", headers=auth(token), json={
            "id": "P_DEL",
            "nombre": "Para borrar",
            "rut": "88.888.888-8",
            "categoria": "Varios"
        })
        r = client.delete("/api/proveedores/P_DEL", headers=auth(token))
        assert r.status_code == 200
        # No aparece en listado
        rlist = client.get("/api/proveedores", headers=auth(token))
        assert "P_DEL" not in [p["id"] for p in rlist.json()]


# ══════════════════════════════════════════════════════════════════
#  ÓRDENES
# ══════════════════════════════════════════════════════════════════

class TestOrdenes:
    def test_create_orden(self):
        token = get_token("vsoto", "super456")
        r = client.post("/api/ordenes", headers=auth(token), json={
            "proveedor_id": "P001",
            "producto": "Leche 1L",
            "cantidad": 100,
            "precio": 800,
            "fecha": "2025-12-01",
            "estado": "pendiente"
        })
        assert r.status_code == 201
        assert "id" in r.json()

    def test_create_orden_auto_id(self):
        token = get_token()
        r = client.post("/api/ordenes", headers=auth(token), json={
            "proveedor_id": "P001",
            "producto": "Mantequilla",
            "cantidad": 50,
            "precio": 1200,
            "fecha": "2025-12-15"
        })
        assert r.status_code == 201
        assert r.json()["id"].startswith("OC-")

    def test_list_ordenes(self):
        token = get_token()
        r = client.get("/api/ordenes", headers=auth(token))
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_ordenes_by_proveedor(self):
        token = get_token()
        r = client.get("/api/ordenes?proveedor_id=P001", headers=auth(token))
        assert r.status_code == 200
        assert all(o["proveedor_id"] == "P001" for o in r.json())

    def test_list_ordenes_forbidden_cajero(self):
        token = get_token("rfuentes", "caja789")
        r = client.get("/api/ordenes", headers=auth(token))
        assert r.status_code == 403

    def test_update_orden(self):
        token = get_token()
        # Crear orden para actualizar
        cr = client.post("/api/ordenes", headers=auth(token), json={
            "id": "OC-UPD",
            "proveedor_id": "P001",
            "producto": "Test",
            "cantidad": 10,
            "precio": 500,
            "fecha": "2025-11-01"
        })
        r = client.patch("/api/ordenes/OC-UPD", headers=auth(token),
                         json={"estado": "recibida"})
        assert r.status_code == 200

    def test_delete_orden(self):
        token = get_token()
        client.post("/api/ordenes", headers=auth(token), json={
            "id": "OC-DEL",
            "proveedor_id": "P001",
            "producto": "Borrar",
            "cantidad": 5,
            "precio": 100,
            "fecha": "2025-11-01"
        })
        r = client.delete("/api/ordenes/OC-DEL", headers=auth(token))
        assert r.status_code == 200


# ══════════════════════════════════════════════════════════════════
#  VENTAS
# ══════════════════════════════════════════════════════════════════

class TestVentas:
    def test_create_venta_ok(self):
        token = get_token("rfuentes", "caja789")
        r = client.post("/api/ventas", headers=auth(token), json={
            "total": 1500,
            "metodo_pago": "Efectivo",
            "items": [
                {"producto_id": "PROD001", "nombre": "Leche Entera",
                 "cantidad": 1, "precio": 1500, "descuento": 0}
            ]
        })
        assert r.status_code == 201
        assert "id" in r.json()

    def test_create_venta_descuenta_stock(self):
        token_admin = get_token()
        stock_antes = client.get("/api/productos/PROD002", headers=auth(token_admin)).json()["stock"]
        token_cajero = get_token("rfuentes", "caja789")
        client.post("/api/ventas", headers=auth(token_cajero), json={
            "total": 400,
            "metodo_pago": "Tarjeta",
            "items": [
                {"producto_id": "PROD002", "nombre": "Pan Marraqueta",
                 "cantidad": 2, "precio": 200, "descuento": 0}
            ]
        })
        stock_despues = client.get("/api/productos/PROD002", headers=auth(token_admin)).json()["stock"]
        assert stock_despues == stock_antes - 2

    def test_create_venta_stock_insuficiente(self):
        token = get_token("rfuentes", "caja789")
        r = client.post("/api/ventas", headers=auth(token), json={
            "total": 5000,
            "metodo_pago": "Efectivo",
            "items": [
                {"producto_id": "PROD003", "nombre": "Stock Crítico",
                 "cantidad": 999, "precio": 500, "descuento": 0}
            ]
        })
        assert r.status_code == 400
        assert "Stock insuficiente" in r.json()["detail"]

    def test_create_venta_producto_inexistente(self):
        token = get_token("rfuentes", "caja789")
        r = client.post("/api/ventas", headers=auth(token), json={
            "total": 100,
            "metodo_pago": "Efectivo",
            "items": [
                {"producto_id": "NOEXISTE", "nombre": "X",
                 "cantidad": 1, "precio": 100, "descuento": 0}
            ]
        })
        assert r.status_code == 404

    def test_list_ventas(self):
        token = get_token("vsoto", "super456")
        r = client.get("/api/ventas", headers=auth(token))
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_ventas_forbidden_cajero(self):
        token = get_token("rfuentes", "caja789")
        r = client.get("/api/ventas", headers=auth(token))
        assert r.status_code == 403

    def test_get_venta_detalle(self):
        # Crear una venta primero
        token = get_token("rfuentes", "caja789")
        cr = client.post("/api/ventas", headers=auth(token), json={
            "total": 1500,
            "metodo_pago": "Transferencia",
            "items": [
                {"producto_id": "PROD001", "nombre": "Leche",
                 "cantidad": 1, "precio": 1500, "descuento": 0}
            ]
        })
        vid = cr.json()["id"]
        r = client.get(f"/api/ventas/{vid}/detalle", headers=auth(token))
        assert r.status_code == 200
        assert "items" in r.json()
        assert len(r.json()["items"]) == 1

    def test_get_venta_detalle_not_found(self):
        token = get_token()
        r = client.get("/api/ventas/99999/detalle", headers=auth(token))
        assert r.status_code == 404


# ══════════════════════════════════════════════════════════════════
#  TURNOS
# ══════════════════════════════════════════════════════════════════

class TestTurnos:
    def test_create_turno(self):
        token = get_token("vsoto", "super456")
        r = client.post("/api/turnos", headers=auth(token), json={
            "cajero_id": 3,
            "hora_inicio": "08:00",
            "estado": "activo"
        })
        assert r.status_code == 201
        assert "id" in r.json()

    def test_list_turnos(self):
        token = get_token("vsoto", "super456")
        r = client.get("/api/turnos", headers=auth(token))
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_turnos_forbidden_cajero(self):
        token = get_token("rfuentes", "caja789")
        r = client.get("/api/turnos", headers=auth(token))
        assert r.status_code == 403

    def test_update_turno(self):
        token = get_token("vsoto", "super456")
        cr = client.post("/api/turnos", headers=auth(token), json={
            "cajero_id": 3,
            "hora_inicio": "14:00",
            "estado": "activo"
        })
        tid = cr.json()["id"]
        r = client.patch(f"/api/turnos/{tid}", headers=auth(token),
                         json={"estado": "cerrado", "hora_fin": "22:00"})
        assert r.status_code == 200

    def test_update_turno_no_fields(self):
        token = get_token()
        r = client.patch("/api/turnos/1", headers=auth(token), json={})
        assert r.status_code == 400

    def test_delete_turno(self):
        token = get_token("vsoto", "super456")
        cr = client.post("/api/turnos", headers=auth(token), json={
            "cajero_id": 3,
            "hora_inicio": "20:00"
        })
        tid = cr.json()["id"]
        r = client.delete(f"/api/turnos/{tid}", headers=auth(token))
        assert r.status_code == 200


# ══════════════════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════════════════

class TestDashboard:
    def test_dashboard_admin(self):
        token = get_token()
        r = client.get("/api/dashboard", headers=auth(token))
        assert r.status_code == 200
        data = r.json()
        assert "ventas_hoy_total" in data
        assert "ventas_hoy_count" in data
        assert "total_productos" in data
        assert "criticos" in data
        assert "bajos" in data
        assert "ordenes_pendientes" in data
        assert "ultimas_ventas" in data
        assert "top_productos" in data

    def test_dashboard_cajero(self):
        token = get_token("rfuentes", "caja789")
        r = client.get("/api/dashboard", headers=auth(token))
        assert r.status_code == 200

    def test_dashboard_sin_token(self):
        r = client.get("/api/dashboard")
        assert r.status_code in (401, 403)  # FastAPI devuelve 401 sin token

    def test_dashboard_productos_count(self):
        token = get_token()
        r = client.get("/api/dashboard", headers=auth(token))
        assert r.json()["total_productos"] >= 3  # Al menos los 3 activos del seed

    def test_dashboard_criticos_count(self):
        token = get_token()
        r = client.get("/api/dashboard", headers=auth(token))
        assert r.json()["criticos"] >= 1  # PROD003 tiene stock=3


# ══════════════════════════════════════════════════════════════════
#  SEGURIDAD / PERMISOS
# ══════════════════════════════════════════════════════════════════

class TestSeguridad:
    def test_no_token_rechazado(self):
        endpoints = [
            "/api/usuarios", "/api/productos", "/api/proveedores",
            "/api/ordenes", "/api/dashboard"
        ]
        for ep in endpoints:
            r = client.get(ep)
            assert r.status_code in (401, 403), f"Endpoint {ep} debería requerir auth (got {r.status_code})"

    def test_token_expirado_rechazado(self):
        import jwt as pyjwt
        from datetime import datetime, timedelta
        expired = pyjwt.encode(
            {"sub": "1", "rol": "admin", "exp": datetime.utcnow() - timedelta(hours=1)},
            "test-secret-key", algorithm="HS256"
        )
        r = client.get("/api/dashboard", headers={"Authorization": f"Bearer {expired}"})
        assert r.status_code == 401

    def test_password_no_expuesto_en_lista(self):
        token = get_token()
        r = client.get("/api/usuarios", headers=auth(token))
        for u in r.json():
            assert "password" not in u

    def test_cajero_no_puede_crear_usuario(self):
        token = get_token("rfuentes", "caja789")
        r = client.post("/api/usuarios", headers=auth(token), json={
            "nombre": "X", "usuario": "x_user", "password": "x", "rol": "cajero"
        })
        assert r.status_code == 403

    def test_cajero_no_puede_ver_proveedores(self):
        token = get_token("rfuentes", "caja789")
        assert client.get("/api/proveedores", headers=auth(token)).status_code == 403

    def test_cajero_no_puede_crear_producto(self):
        token = get_token("rfuentes", "caja789")
        r = client.post("/api/productos", headers=auth(token), json={
            "id": "SEC_X", "nombre": "X", "categoria": "X",
            "precio": 1, "costo": 1, "stock": 1, "stock_min": 1
        })
        assert r.status_code == 403

    def test_supervisor_no_puede_crear_usuario(self):
        token = get_token("vsoto", "super456")
        r = client.post("/api/usuarios", headers=auth(token), json={
            "nombre": "X", "usuario": "x_sup", "password": "x", "rol": "cajero"
        })
        assert r.status_code == 403

# ══════════════════════════════════════════════════════════════════
#  HISTORIAL DE VENTAS
# ══════════════════════════════════════════════════════════════════

class TestSalesHistory:
    """Tests para GET /api/sales/history y /api/sales/summary"""

    @classmethod
    def _seed_venta(cls, token_cajero):
        """Crea una venta de prueba y retorna su id."""
        r = client.post("/api/ventas", headers=auth(token_cajero), json={
            "total": 1000,
            "metodo_pago": "Efectivo",
            "items": [
                {"producto_id": "PROD002", "nombre": "Pan Marraqueta",
                 "cantidad": 1, "precio": 1000, "descuento": 0}
            ]
        })
        assert r.status_code == 201, r.text
        return r.json()["id"]

    def test_history_requires_auth(self):
        r = client.get("/api/sales/history")
        assert r.status_code in (401, 403)

    def test_history_forbidden_cajero(self):
        token = get_token("rfuentes", "caja789")
        r = client.get("/api/sales/history", headers=auth(token))
        assert r.status_code == 403

    def test_history_supervisor_ok(self):
        token = get_token("vsoto", "super456")
        r = client.get("/api/sales/history", headers=auth(token))
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert "data" in data
        assert "pagination" in data
        assert isinstance(data["data"], list)

    def test_history_admin_ok(self):
        token = get_token()
        r = client.get("/api/sales/history", headers=auth(token))
        assert r.status_code == 200

    def test_history_period_today(self):
        # Primero crear una venta
        cajero_token = get_token("rfuentes", "caja789")
        self._seed_venta(cajero_token)
        token = get_token("vsoto", "super456")
        r = client.get("/api/sales/history?period=today", headers=auth(token))
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert len(data["data"]) >= 1

    def test_history_period_week(self):
        token = get_token("vsoto", "super456")
        r = client.get("/api/sales/history?period=week", headers=auth(token))
        assert r.status_code == 200
        assert r.json()["success"] is True

    def test_history_period_month(self):
        token = get_token("vsoto", "super456")
        r = client.get("/api/sales/history?period=month", headers=auth(token))
        assert r.status_code == 200
        assert r.json()["success"] is True

    def test_history_invalid_period(self):
        token = get_token("vsoto", "super456")
        r = client.get("/api/sales/history?period=yesterday", headers=auth(token))
        assert r.status_code == 400

    def test_history_date_range(self):
        token = get_token("vsoto", "super456")
        r = client.get("/api/sales/history?start_date=2020-01-01&end_date=2099-12-31", headers=auth(token))
        assert r.status_code == 200
        assert r.json()["success"] is True

    def test_history_invalid_date_format(self):
        token = get_token("vsoto", "super456")
        r = client.get("/api/sales/history?start_date=31/12/2025", headers=auth(token))
        assert r.status_code == 400

    def test_history_no_results_range(self):
        token = get_token("vsoto", "super456")
        r = client.get("/api/sales/history?start_date=2000-01-01&end_date=2000-01-02", headers=auth(token))
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert data["data"] == []
        assert data["pagination"]["total"] == 0

    def test_history_pagination_structure(self):
        token = get_token("vsoto", "super456")
        r = client.get("/api/sales/history?per_page=5&page=1", headers=auth(token))
        assert r.status_code == 200
        pag = r.json()["pagination"]
        assert "page" in pag
        assert "per_page" in pag
        assert "total" in pag
        assert "pages" in pag

    def test_history_invalid_page(self):
        token = get_token("vsoto", "super456")
        r = client.get("/api/sales/history?page=0", headers=auth(token))
        assert r.status_code == 400

    def test_history_row_fields(self):
        # Crear venta y verificar campos en respuesta
        cajero_token = get_token("rfuentes", "caja789")
        self._seed_venta(cajero_token)
        token = get_token("vsoto", "super456")
        r = client.get("/api/sales/history?period=today", headers=auth(token))
        rows = r.json()["data"]
        assert len(rows) > 0
        row = rows[0]
        for field in ("id", "total", "metodo_pago", "creado", "cajero_nombre", "num_productos"):
            assert field in row, f"Campo '{field}' faltante"

    def test_summary_requires_auth(self):
        r = client.get("/api/sales/summary")
        assert r.status_code in (401, 403)

    def test_summary_forbidden_cajero(self):
        token = get_token("rfuentes", "caja789")
        r = client.get("/api/sales/summary", headers=auth(token))
        assert r.status_code == 403

    def test_summary_ok(self):
        token = get_token("vsoto", "super456")
        r = client.get("/api/sales/summary", headers=auth(token))
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert "total_vendido" in data["data"]
        assert "cantidad_ventas" in data["data"]
        assert "ticket_promedio" in data["data"]

    def test_summary_period_today_values(self):
        # Asegurar al menos 1 venta hoy
        cajero_token = get_token("rfuentes", "caja789")
        self._seed_venta(cajero_token)
        token = get_token("vsoto", "super456")
        r = client.get("/api/sales/summary?period=today", headers=auth(token))
        data = r.json()["data"]
        assert data["total_vendido"] > 0
        assert data["cantidad_ventas"] >= 1

    def test_summary_empty_range(self):
        token = get_token("vsoto", "super456")
        r = client.get("/api/sales/summary?start_date=2000-01-01&end_date=2000-01-02", headers=auth(token))
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["total_vendido"] == 0
        assert data["cantidad_ventas"] == 0

    def test_summary_invalid_period(self):
        token = get_token("vsoto", "super456")
        r = client.get("/api/sales/summary?period=badvalue", headers=auth(token))
        assert r.status_code == 400

# ══════════════════════════════════════════════════════════════════
#  PERFIL & CONFIGURACIÓN DE CORREO
# ══════════════════════════════════════════════════════════════════

class TestProfile:
    """Tests para GET/PATCH /api/auth/profile y POST /api/auth/test-email"""

    def test_get_profile_requires_auth(self):
        r = client.get("/api/auth/profile")
        assert r.status_code in (401, 403)

    def test_get_profile_admin(self):
        token = get_token()
        r = client.get("/api/auth/profile", headers=auth(token))
        assert r.status_code == 200
        data = r.json()
        assert data["usuario"] == "admin"
        assert data["rol"] == "admin"
        assert "smtp_email" in data
        assert "notif_email_admin" in data
        assert "smtp_configured" in data
        assert "password" not in data

    def test_get_profile_cajero_no_email_fields(self):
        token = get_token("rfuentes", "caja789")
        r = client.get("/api/auth/profile", headers=auth(token))
        assert r.status_code == 200
        data = r.json()
        assert "smtp_email" not in data
        assert "smtp_app_password" not in data

    def test_patch_profile_nombre(self):
        token = get_token()
        r = client.patch("/api/auth/profile", headers=auth(token), json={"nombre": "Carlos Admin"})
        assert r.status_code == 200
        # Verificar que cambió
        profile = client.get("/api/auth/profile", headers=auth(token)).json()
        assert profile["nombre"] == "Carlos Admin"
        # Restaurar
        client.patch("/api/auth/profile", headers=auth(token), json={"nombre": "Carlos Mendoza"})

    def test_patch_profile_smtp_config(self):
        token = get_token()
        r = client.patch("/api/auth/profile", headers=auth(token), json={
            "smtp_email": "test@gmail.com",
            "smtp_app_password": "testpass1234",
            "notif_email_admin": "admin@freshmart.cl"
        })
        assert r.status_code == 200
        profile = client.get("/api/auth/profile", headers=auth(token)).json()
        assert profile["smtp_email"] == "test@gmail.com"
        assert profile["smtp_configured"] is True

    def test_patch_profile_smtp_forbidden_for_cajero(self):
        token = get_token("rfuentes", "caja789")
        r = client.patch("/api/auth/profile", headers=auth(token), json={
            "smtp_email": "hacker@gmail.com"
        })
        assert r.status_code == 403

    def test_cajero_can_update_own_nombre(self):
        token = get_token("rfuentes", "caja789")
        r = client.patch("/api/auth/profile", headers=auth(token), json={"nombre": "Rodrigo F."})
        assert r.status_code == 200
        # Restaurar
        client.patch("/api/auth/profile", headers=auth(token), json={"nombre": "Rodrigo Fuentes"})

    def test_test_email_requires_admin(self):
        token = get_token("vsoto", "super456")
        r = client.post("/api/auth/test-email", headers=auth(token), json={
            "smtp_email": "x@gmail.com",
            "smtp_app_password": "xxx",
            "notif_email_admin": "dest@mail.com"
        })
        assert r.status_code == 403

    def test_test_email_empty_fields_returns_400(self):
        token = get_token()
        r = client.post("/api/auth/test-email", headers=auth(token), json={
            "smtp_email": "",
            "smtp_app_password": "",
            "notif_email_admin": ""
        })
        assert r.status_code == 400

    def test_test_email_bad_credentials_returns_400(self):
        """Con credenciales inválidas el servidor SMTP rechaza → 400"""
        token = get_token()
        r = client.post("/api/auth/test-email", headers=auth(token), json={
            "smtp_email": "invalid@gmail.com",
            "smtp_app_password": "wrongpassword",
            "notif_email_admin": "dest@mail.com"
        })
        # Debe ser 400 (auth error o conexión rechazada), no 500
        assert r.status_code == 400


class TestStockAlerts:
    """Tests para GET /api/notifications/stock-alerts"""

    def test_stock_alerts_requires_auth(self):
        r = client.get("/api/notifications/stock-alerts")
        assert r.status_code in (401, 403)

    def test_stock_alerts_forbidden_cajero(self):
        token = get_token("rfuentes", "caja789")
        r = client.get("/api/notifications/stock-alerts", headers=auth(token))
        assert r.status_code == 403

    def test_stock_alerts_supervisor_ok(self):
        token = get_token("vsoto", "super456")
        r = client.get("/api/notifications/stock-alerts", headers=auth(token))
        assert r.status_code == 200
        data = r.json()
        assert "data" in data
        assert "total" in data
        assert isinstance(data["data"], list)

    def test_stock_alerts_admin_ok(self):
        token = get_token()
        r = client.get("/api/notifications/stock-alerts", headers=auth(token))
        assert r.status_code == 200

    def test_stock_alerts_all_below_min(self):
        """Todos los productos retornados deben tener stock <= stock_min"""
        token = get_token()
        r = client.get("/api/notifications/stock-alerts", headers=auth(token))
        for prod in r.json()["data"]:
            assert prod["stock"] <= prod["stock_min"], \
                f"{prod['nombre']}: stock {prod['stock']} > stock_min {prod['stock_min']}"

    def test_stock_alerts_fields(self):
        token = get_token()
        r = client.get("/api/notifications/stock-alerts", headers=auth(token))
        for prod in r.json()["data"]:
            for field in ("id", "nombre", "categoria", "icono", "stock", "stock_min"):
                assert field in prod, f"Campo '{field}' faltante en alerta de stock"