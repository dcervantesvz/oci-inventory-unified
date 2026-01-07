# -*- coding: utf-8 -*-
"""
Nombre del Proyecto: oci-inventory-unified
Autor: Daniel de Jesús Cervantes Velázquez
Equipo: Automatización OCI
Licencia: MIT
"""
import smtplib
import mimetypes
import os
from email.message import EmailMessage
from typing import List, Optional
from cryptography.fernet import Fernet

def send_email(
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,      # Viene encriptado del config.ini
    smtp_password: str,  # Viene encriptado del config.ini
    sender: str,
    recipients: List[str],
    subject: str,
    body: str,
    attachment_path: Optional[str] = None,
) -> None:
    """Envía un correo electrónico desencriptando las credenciales al vuelo."""
    
    # 1. Proceso de Desencriptación
    try:
        key_path = ".key"
        if not os.path.exists(key_path):
            raise FileNotFoundError(f"Error: No se encontró el archivo {key_path}")

        with open(key_path, "rb") as f:
            key = f.read()

        cipher = Fernet(key)
        # Desencriptamos los valores que vienen del config.ini
        real_user = cipher.decrypt(smtp_user.encode()).decode()
        real_password = cipher.decrypt(smtp_password.encode()).decode()
    except Exception as e:
        print(f"❌ Error crítico de seguridad: {e}")
        raise

    # 2. Configuración del mensaje
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.set_content(body)

    # 3. Adjuntar el archivo Excel si existe
    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as f:
            file_data = f.read()
            ctype, encoding = mimetypes.guess_type(attachment_path)
            maintype, subtype = (ctype or "application/octet-stream").split("/", 1)
            msg.add_attachment(
                file_data,
                maintype=maintype,
                subtype=subtype,
                filename=os.path.basename(attachment_path)
            )

    # 4. Conexión SMTP Segura
    try:
        # Usamos rutas explícitas para evitar errores en sesiones CRON
        with smtplib.SMTP(smtp_host, int(smtp_port)) as smtp:
            smtp.ehlo()
            smtp.starttls()  # Requerido para puerto 587
            smtp.ehlo()

            smtp.login(real_user, real_password)
            smtp.send_message(msg)

        print("📧 Reporte enviado exitosamente con credenciales protegidas.")
    except Exception as e:
        print(f"❌ Error en la conexión SMTP: {e}")
        raise