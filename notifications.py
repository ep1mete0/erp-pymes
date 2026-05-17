"""
FreshMart — Envío de notificaciones (correo / WhatsApp).

Configuración opcional por variables de entorno:
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM
  TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM

Sin configuración, las notificaciones se registran en logs (modo desarrollo).
"""

import logging
import os
import re
import smtplib
from email.mime.text import MIMEText
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

logger = logging.getLogger("freshmart.notifications")

NOTIF_PREFS = ("email", "whatsapp", "ambos")


def normalize_cl_phone(phone: Optional[str]) -> Optional[str]:
    """Normaliza celular chileno a formato E.164 +569XXXXXXXX."""
    if not phone:
        return None
    digits = re.sub(r"\D", "", phone.strip())
    if digits.startswith("56"):
        digits = digits[2:]
    if digits.startswith("0"):
        digits = digits[1:]
    if len(digits) == 8 and digits[0] in "23456789":
        digits = "9" + digits
    if len(digits) == 9 and digits[0] == "9":
        return "+56" + digits
    if len(digits) == 11 and digits.startswith("569"):
        return "+" + digits
    return None


def validate_cl_phone(phone: Optional[str]) -> bool:
    n = normalize_cl_phone(phone)
    return n is not None and re.fullmatch(r"\+569\d{8}", n) is not None


def validate_email(email: Optional[str]) -> bool:
    if not email or not email.strip():
        return True
    return re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()) is not None


def _send_email(to: str, subject: str, body: str) -> bool:
    host = os.getenv("SMTP_HOST")
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    from_addr = os.getenv("SMTP_FROM", user or "noreply@freshmart.local")
    port = int(os.getenv("SMTP_PORT", "587"))

    if not host or not user or not password:
        logger.info("[EMAIL → %s] %s\n%s", to, subject, body)
        return True

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to
    try:
        with smtplib.SMTP(host, port, timeout=15) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(from_addr, [to], msg.as_string())
        return True
    except Exception as exc:
        logger.error("Error enviando email a %s: %s", to, exc)
        return False


def _send_whatsapp(to_e164: str, body: str) -> bool:
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    from_num = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

    if not sid or not token:
        logger.info("[WHATSAPP → %s] %s", to_e164, body)
        return True

    to_wa = to_e164 if to_e164.startswith("whatsapp:") else f"whatsapp:{to_e164}"
    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    data = urlencode({
        "From": from_num,
        "To": to_wa,
        "Body": body,
    }).encode()
    req = Request(url, data=data, method="POST")
    import base64
    creds = base64.b64encode(f"{sid}:{token}".encode()).decode()
    req.add_header("Authorization", f"Basic {creds}")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urlopen(req, timeout=20) as resp:
            return 200 <= resp.status < 300
    except (HTTPError, URLError) as exc:
        logger.error("Error enviando WhatsApp a %s: %s", to_e164, exc)
        return False


def stock_alert_message(producto: dict) -> str:
    stock = producto.get("stock", 0)
    stock_min = producto.get("stock_min", 0)
    nombre = producto.get("nombre", producto.get("id", "Producto"))
    nivel = "crítico" if stock <= 5 else "bajo"
    return (
        f"FreshMart — Alerta de stock {nivel}\n\n"
        f"Producto: {nombre}\n"
        f"Stock actual: {stock} unidades\n"
        f"Stock mínimo configurado: {stock_min}\n\n"
        f"Revisa el inventario y repón a la brevedad."
    )


def notify_user_stock_alert(
    usuario: dict,
    producto: dict,
    conn=None,
) -> None:
    """Envía alerta según preferencia del usuario (email / whatsapp / ambos)."""
    pref = (usuario.get("notif_pref") or "email").lower()
    if pref not in NOTIF_PREFS:
        pref = "email"

    msg = stock_alert_message(producto)
    subject = f"FreshMart — Stock bajo: {producto.get('nombre', 'Producto')}"
    email = (usuario.get("email") or "").strip()
    phone = normalize_cl_phone(usuario.get("telefono"))

    canales = []
    if pref in ("email", "ambos") and email:
        canales.append(("email", email))
    if pref in ("whatsapp", "ambos") and phone:
        canales.append(("whatsapp", phone))

    if not canales:
        return

    for canal, destino in canales:
        ok = False
        if canal == "email":
            ok = _send_email(destino, subject, msg)
        else:
            ok = _send_whatsapp(destino, msg)

        if conn is not None:
            try:
                conn.execute(
                    """INSERT INTO notificaciones_log
                       (usuario_id, producto_id, canal, destino, mensaje, estado)
                       VALUES (?,?,?,?,?,?)""",
                    (
                        usuario["id"],
                        producto.get("id"),
                        canal,
                        destino,
                        msg[:500],
                        "enviado" if ok else "error",
                    ),
                )
            except Exception:
                pass


def should_notify_stock_crossing(old_stock: int, new_stock: int, stock_min: int) -> bool:
    """Notificar solo al cruzar por debajo del stock mínimo (evita spam)."""
    if stock_min <= 0:
        return False
    if new_stock > stock_min:
        return False
    if old_stock <= stock_min:
        return False
    return True
