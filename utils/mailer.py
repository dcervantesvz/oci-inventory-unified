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

def send_email(
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    sender: str,
    recipients: List[str],
    subject: str,
    body: str,
    attachment_path: Optional[str] = None,
) -> None:
    """Envía un correo electrónico con un adjunto usando EmailMessage."""
    
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.set_content(body)

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

    # Conexión y envío
    try:
        # OCI suele usar puerto 587 con STARTTLS
        with smtplib.SMTP(smtp_host, smtp_port) as smtp:
            smtp.starttls()
            if smtp_user and smtp_password:
                smtp.login(smtp_user, smtp_password)
            smtp.send_message(msg)
        print("✅ Correo enviado correctamente.")
    except Exception as e:
        print(f"❌ Error enviando correo: {e}")
        raise