#!/usr/bin/env python3
"""
FreshMart ERP — Inicialización de base de datos
Ejecutar UNA VEZ para crear tablas e insertar datos iniciales.
Uso: python init_db.py
"""

import sqlite3
import hashlib
import os
from datetime import date

DB_PATH = "./database.db"


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def main():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # ─── USUARIOS ───────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre    TEXT    NOT NULL,
        usuario   TEXT    NOT NULL UNIQUE,
        password  TEXT    NOT NULL,
        rol       TEXT    NOT NULL CHECK(rol IN ('admin','supervisor','cajero')),
        pin       TEXT    NOT NULL DEFAULT '0000',
        activo    INTEGER NOT NULL DEFAULT 1,
        creado    TEXT    NOT NULL DEFAULT (date('now'))
    )
    """)

    # ─── PRODUCTOS / INVENTARIO ──────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS productos (
        id        TEXT    PRIMARY KEY,
        nombre    TEXT    NOT NULL,
        categoria TEXT    NOT NULL,
        icono     TEXT    NOT NULL DEFAULT '📦',
        precio    REAL    NOT NULL DEFAULT 0,
        costo     REAL    NOT NULL DEFAULT 0,
        stock     INTEGER NOT NULL DEFAULT 0,
        stock_min INTEGER NOT NULL DEFAULT 0,
        vencimiento TEXT,
        descuento REAL    NOT NULL DEFAULT 0,
        activo    INTEGER NOT NULL DEFAULT 1,
        creado    TEXT    NOT NULL DEFAULT (datetime('now'))
    )
    """)

    # ─── PROVEEDORES ─────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS proveedores (
        id            TEXT    PRIMARY KEY,
        nombre        TEXT    NOT NULL,
        rut           TEXT    NOT NULL,
        categoria     TEXT    NOT NULL,
        contacto      TEXT,
        telefono      TEXT,
        email         TEXT,
        direccion     TEXT,
        plazo_pago    INTEGER NOT NULL DEFAULT 30,
        frecuencia    TEXT    NOT NULL DEFAULT 'Semanal',
        notas         TEXT,
        compras_mes   REAL    NOT NULL DEFAULT 0,
        compras_total REAL    NOT NULL DEFAULT 0,
        activo        INTEGER NOT NULL DEFAULT 1
    )
    """)

    # ─── ÓRDENES DE COMPRA ───────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS ordenes (
        id          TEXT    PRIMARY KEY,
        proveedor_id TEXT   NOT NULL REFERENCES proveedores(id),
        producto    TEXT    NOT NULL,
        cantidad    INTEGER NOT NULL,
        precio      REAL    NOT NULL,
        fecha       TEXT    NOT NULL,
        estado      TEXT    NOT NULL DEFAULT 'pendiente'
                    CHECK(estado IN ('pendiente','recibida','parcial','cancelada')),
        notas       TEXT,
        creado      TEXT    NOT NULL DEFAULT (datetime('now'))
    )
    """)

    # ─── VENTAS ──────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS ventas (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        cajero_id   INTEGER NOT NULL REFERENCES usuarios(id),
        total       REAL    NOT NULL,
        metodo_pago TEXT    NOT NULL DEFAULT 'Efectivo',
        creado      TEXT    NOT NULL DEFAULT (datetime('now'))
    )
    """)

    # ─── DETALLE VENTAS ──────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS detalle_ventas (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        venta_id    INTEGER NOT NULL REFERENCES ventas(id),
        producto_id TEXT    NOT NULL,
        nombre      TEXT    NOT NULL,
        cantidad    INTEGER NOT NULL,
        precio      REAL    NOT NULL,
        descuento   REAL    NOT NULL DEFAULT 0
    )
    """)

    # ─── TURNOS ──────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS turnos (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        cajero_id   INTEGER NOT NULL REFERENCES usuarios(id),
        fecha       TEXT    NOT NULL DEFAULT (date('now')),
        hora_inicio TEXT    NOT NULL,
        hora_fin    TEXT,
        estado      TEXT    NOT NULL DEFAULT 'activo'
                    CHECK(estado IN ('activo','cerrado','ausente')),
        notas       TEXT
    )
    """)

    # ─── REPOSICIONES / MOVIMIENTOS DE STOCK ────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS reposiciones (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        producto_id TEXT    NOT NULL REFERENCES productos(id),
        cantidad    INTEGER NOT NULL,
        proveedor   TEXT,
        nota        TEXT,
        creado      TEXT    NOT NULL DEFAULT (datetime('now'))
    )
    """)

    conn.commit()

    # ═══════════════════════════════════════════════════════════
    # DATOS INICIALES
    # ═══════════════════════════════════════════════════════════

    # Solo insertar si las tablas están vacías
    if c.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
        print("📥 Insertando usuarios iniciales...")
        usuarios = [
            ("Carlos Mendoza",  "admin",    hash_password(
                "admin123"),    "admin",      "1234", 1, "01/04/2026"),
            ("Valeria Soto",    "vsoto",    hash_password(
                "super456"),    "supervisor", "2580", 1, "05/04/2026"),
            ("Rodrigo Fuentes", "rfuentes", hash_password(
                "caja789"),     "cajero",     "7391", 1, "10/04/2026"),
            ("Pamela Torres",   "ptorres",  hash_password(
                "caja321"),     "cajero",     "4567", 1, "12/04/2026"),
            ("Miguel Ríos",     "mrios",    hash_password(
                "caja000"),     "cajero",     "8823", 0, "18/04/2026"),
        ]
        c.executemany(
            "INSERT INTO usuarios (nombre, usuario, password, rol, pin, activo, creado) VALUES (?,?,?,?,?,?,?)",
            usuarios
        )
        print("  ✅ 5 usuarios creados. Usuario admin: admin / admin123")

    if c.execute("SELECT COUNT(*) FROM productos").fetchone()[0] == 0:
        print("📥 Insertando productos iniciales...")
        productos = [
            ("7801005001", "Leche Entera 1L",      "Lácteos",
             "🥛", 1290, 850, 48, 20, "2026-08-15", 0),
            ("7801005002", "Yogur Frutilla 165g",   "Lácteos",
             "🍶", 650, 380,  7, 15, "2026-07-10", 0),
            ("7801005003", "Mantequilla 200g",       "Lácteos",
             "🧈", 2190, 1400, 20, 10, "2026-09-01", 0),
            ("7801007001", "Pan Molde 550g",          "Panadería",
             "🍞", 1890, 1100,  3, 10, "2026-07-05", 0),
            ("7801007002", "Hallulla x6",             "Panadería",
             "🥖", 990, 550, 30, 15, "2026-07-06", 10),
            ("7801009001", "Manzana Royal Gala kg",   "Frutas",
             "🍎", 1490, 900, 60, 20, "2026-07-20", 0),
            ("7801009002", "Plátano kg",              "Frutas",
             "🍌", 890, 500, 40, 15, "2026-07-12", 5),
            ("7801009003", "Tomate kg",               "Verduras",
             "🍅", 1190, 700, 50, 20, "2026-07-15", 0),
            ("7801009004", "Zanahoria kg",            "Verduras",
             "🥕", 690, 380, 35, 15, "2026-07-25", 0),
            ("7801009005", "Lechuga un.",             "Verduras",
             "🥬", 990, 500,  4, 10, "2026-07-08", 15),
            ("7801011001", "Pechuga Pollo kg",        "Carnes",
             "🍗", 5990, 3800, 18, 8, "2026-07-07", 0),
            ("7801011002", "Carne Molida kg",         "Carnes",
             "🥩", 6990, 4500,  2, 8, "2026-07-06", 0),
            ("7801013001", "Coca-Cola 1.5L",          "Bebidas",
             "🥤", 1490, 850, 55, 25, "2027-03-10", 0),
            ("7801013002", "Agua Mineral 1.5L",       "Bebidas",
             "💧", 590, 280, 80, 30, "2027-06-01", 0),
            ("7801013003", "Jugo Natural 1L",         "Bebidas",
             "🧃", 1790, 1100, 25, 12, "2026-08-20", 10),
            ("7801015001", "Arroz Grado 1 1kg",       "Abarrotes",
             "🍚", 1390, 850, 40, 20, "2027-01-01", 0),
            ("7801015002", "Fideos Spaghetti 400g",   "Abarrotes",
             "🍝", 990, 580, 38, 15, "2027-02-01", 0),
            ("7801015003", "Aceite Vegetal 900ml",    "Abarrotes",
             "🫙", 2490, 1600, 28, 12, "2027-04-01", 0),
            ("7801017001", "Detergente 1kg",
             "Limpieza", "🧴", 3490, 2100, 20, 10, None, 0),
            ("7801017002", "Papel Higiénico x4",
             "Limpieza", "🧻", 2190, 1300, 45, 20, None, 5),
        ]
        c.executemany(
            "INSERT INTO productos (id,nombre,categoria,icono,precio,costo,stock,stock_min,vencimiento,descuento) VALUES (?,?,?,?,?,?,?,?,?,?)",
            productos
        )
        print(f"  ✅ {len(productos)} productos creados")

    if c.execute("SELECT COUNT(*) FROM proveedores").fetchone()[0] == 0:
        print("📥 Insertando proveedores iniciales...")
        proveedores = [
            ("P001", "Lácteos del Sur Ltda.",   "76.123.456-7", "Lácteos",          "Pedro Vega",   "+56 9 8765 4321", "pvega@lacteossur.cl",
             "Av. Industrial 500, Temuco", 30, "Diaria", "Entrega antes de las 8am. Descuento 5% en vol. >$500k.", 1280000, 8450000),
            ("P002", "Distribuidora Cereal S.A.", "78.234.567-8", "Abarrotes",        "Ana Torres",   "+56 9 7654 3210",
             "atorres@distcereal.cl",   "Los Aromos 234, Santiago",  60, "Semanal", "Pago a 60 días. Mínimo de pedido $200k.", 560000, 4200000),
            ("P003", "Frutería Andina SpA",      "77.345.678-9", "Frutas y Verduras", "Carlos Rojas", "+56 9 6543 2109", "crojas@fruteriaandina.cl",
             "Mercado Lo Valledor, Stand 45, Santiago", 7, "Diaria", "Pago al contado o transferencia antes de despacho.", 920000, 6100000),
            ("P004", "Carnes Premium SpA",       "76.456.789-0", "Carnes",           "Roberto Muñoz", "+56 9 5432 1098", "rmunoz@carnespremium.cl",
             "Matadero Central, Galpón 3, Renca", 14, "2 veces/semana", "Temperatura controlada garantizada. Factura con guía.", 2340000, 15800000),
            ("P005", "Bebidas Chile S.A.",       "76.567.890-1", "Bebidas",          "Sofía Herrera", "+56 9 4321 0987", "sherrera@bebidachile.cl",
             "Panamericana Norte km 12, Santiago", 30, "Quincenal", "Retornables con garantía. Incluye transporte.", 780000, 5600000),
        ]
        c.executemany(
            "INSERT INTO proveedores (id,nombre,rut,categoria,contacto,telefono,email,direccion,plazo_pago,frecuencia,notas,compras_mes,compras_total) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            proveedores
        )
        print(f"  ✅ {len(proveedores)} proveedores creados")

    if c.execute("SELECT COUNT(*) FROM ordenes").fetchone()[0] == 0:
        print("📥 Insertando órdenes iniciales...")
        ordenes = [
            ("OC-001", "P001", "Leche Entera 1L",        200, 850,
             "2026-07-05", "pendiente", "Urgente para reposición"),
            ("OC-002", "P001", "Yogur Frutilla 165g",
             100, 380, "2026-07-04", "recibida", ""),
            ("OC-003", "P003", "Manzana Royal Gala kg",
             80, 900, "2026-07-03", "recibida", ""),
            ("OC-004", "P004", "Pechuga Pollo kg",          40, 3800,
             "2026-07-06", "pendiente", "Confirmar temperatura"),
            ("OC-005", "P004", "Carne Molida kg",           25,
             4500, "2026-07-04", "parcial", "Recibidos 15 kg"),
            ("OC-006", "P002", "Arroz Grado 1 1kg",
             150, 850, "2026-07-10", "pendiente", ""),
            ("OC-007", "P005", "Coca-Cola 1.5L",
             120, 850, "2026-07-08", "pendiente", ""),
        ]
        c.executemany(
            "INSERT INTO ordenes (id,proveedor_id,producto,cantidad,precio,fecha,estado,notas) VALUES (?,?,?,?,?,?,?,?)",
            ordenes
        )
        print(f"  ✅ {len(ordenes)} órdenes creadas")

    if c.execute("SELECT COUNT(*) FROM turnos").fetchone()[0] == 0:
        print("📥 Insertando turnos de ejemplo...")
        hoy = date.today().isoformat()
        turnos = [
            (3, hoy, "08:00", "16:00", "cerrado", "Turno mañana"),
            (4, hoy, "08:00", "16:00", "cerrado", "Turno mañana"),
            (3, hoy, "16:00", None,    "activo",  "Turno tarde"),
        ]
        c.executemany(
            "INSERT INTO turnos (cajero_id,fecha,hora_inicio,hora_fin,estado,notas) VALUES (?,?,?,?,?,?)",
            turnos
        )
        print(f"  ✅ {len(turnos)} turnos creados")

    conn.commit()
    conn.close()
    print("\n🎉 Base de datos inicializada correctamente en:", DB_PATH)
    print("━" * 50)
    print("  Acceso admin → usuario: admin  |  contraseña: admin123")
    print("━" * 50)

if __name__ == "__main__":
    main()
