# -*- coding: utf-8 -*-
import configparser
import os
from cryptography.fernet import Fernet

def setup():
    print("🔐 Configuración de Seguridad - OCI Inventory")

    # 1. Manejo de la Llave Maestra (.key)
    key_file_path = ".key"
    if not os.path.exists(key_file_path):
        key = Fernet.generate_key()
        with open(key_file_path, "wb") as key_file:
            key_file.write(key)
        print("✅ Nueva llave de seguridad generada en .key")
    else:
        with open(key_file_path, "rb") as key_file:
            key = key_file.read()
        print("ℹ️ Usando llave de seguridad existente.")

    cipher = Fernet(key)

    # 2. Captura de datos por consola
    print("\n--- Ingrese los datos de SMTP (OCI Email Delivery) ---")
    host = input("SMTP Host (ej. smtp.email.us-ashburn-1.oci.oraclecloud.com): ")
    port = input("SMTP Port (ej. 587): ")
    user_raw = input("SMTP User (OCID de las credenciales SMTP): ")
    pass_raw = input("SMTP Password (Contraseña generada): ")
    sender = input("Email Sender (Correo aprobado en OCI): ")
    receiver = input("Email Receiver (Destinatario del reporte): ")

    # 3. Encriptación
    user_enc = cipher.encrypt(user_raw.encode()).decode()
    pass_enc = cipher.encrypt(pass_raw.encode()).decode()

    # 4. Creación del archivo config.ini
    config = configparser.ConfigParser()
    config['SMTP'] = {
        'host': host,
        'port': port,
        'user': user_enc,
        'password': pass_enc,
        'sender': sender,
        'receiver': receiver
    }

    with open('config.ini', 'w') as configfile:
        config.write(configfile)

    print("\n✅ Archivo 'config.ini' generado con éxito.")
    print("⚠️  IMPORTANTE: Asegúrate de que '.key' y 'config.ini' estén en tu .gitignore.")

if __name__ == "__main__":
    setup()