# -*- coding: utf-8 -*-
"""
Nombre del Proyecto: oci-inventory-unified
Autor: Daniel de Jesús Cervantes Velázquez
Equipo: Automatización OCI
Licencia: MIT
"""
import oci
import pandas as pd
import os
import configparser
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# --- IMPORTACIONES CORREGIDAS ---
# Ahora importamos desde el paquete 'core'
from core import compute, dbsystem, buckets, oic_instances, load_balancers, file_storage
from utils.mailer import send_email

def handle_email_delivery(file_path, inventory_results):
    """Envía el correo con el body adaptado para operadores y el resumen de hallazgos."""
    if not os.path.exists("config.ini"):
        print("⚠️ No se encontró config.ini, saltando envío.")
        return

    cp = configparser.ConfigParser()
    cp.read("config.ini", encoding='utf-8')
    
    # Generar lista de servicios incluidos dinámicamente
    servicios_incluidos = ", ".join(inventory_results.keys())

    body_text = f"""Este reporte incluye información relevante para las tareas de monitoreo y control de la infraestructura en OCI. 

El presente inventario unificado contiene detalles de: {servicios_incluidos}.

Por favor, revisar la información adjunta y utilizarla para las actividades correspondientes. Favor de no responder a este mensaje.

En caso de dudas o incidencias, contactar al área de infraestructura.

Saludos cordiales,
Equipo de Automatización OCI"""

    try:
        puerto = int(cp['SMTP']['port'])
        send_email(
            smtp_host=cp['SMTP']['host'],
            smtp_port=puerto,
            smtp_user=cp['SMTP']['user'],
            smtp_password=cp['SMTP']['password'],
            sender=cp['SMTP']['sender'],
            recipients=[cp['SMTP']['receiver']],
            subject=f"Inventario Unificado OCI - {datetime.now().strftime('%d/%m/%Y')}",
            body=body_text,
            attachment_path=file_path
        )
        print("📧 Proceso de notificación finalizado exitosamente.")
    except Exception as e:
        print(f"⚠️ Error al enviar el correo: {e}")

def main():
    start_time = datetime.now()

    # 1. Preparar carpeta de reportes
    reports_dir = "reports"
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)

    # 2. Configuración OCI
    try:
        config = oci.config.from_file("~/.oci/config", "DEFAULT")
        tenancy_id = config["tenancy"]
        identity_client = oci.identity.IdentityClient(config)

        print("🔍 Listando compartimentos...")
        compartments = oci.pagination.list_call_get_all_results(
            identity_client.list_compartments,
            compartment_id=tenancy_id,
            compartment_id_in_subtree=True,
            lifecycle_state="ACTIVE"
        ).data
        compartments.append(oci.identity.models.Compartment(id=tenancy_id, name="root"))
    except Exception as e:
        print(f"❌ Error de autenticación OCI: {e}")
        return

    # 3. Procesamiento paralelo de módulos (usando los módulos de core)
    tasks = [
        # (compute.get_compute_instances, "Compute"),
        # (dbsystem.get_db_systems, "Base de Datos"),
        # (buckets.get_buckets, "Buckets"),
        # (oic_instances.get_oic_instances, "OIC"),
        # (load_balancers.get_load_balancers, "LoadBalancers"),
        (file_storage.get_file_systems, "FileStorage")
    ]

    inventory_results = {}
    print(f"⚙️ Procesando {len(tasks)} servicios en paralelo...")
    
    with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
        # Submit de tareas
        future_to_sheet = {executor.submit(func, config, compartments): sheet for func, sheet in tasks}
        
        for future in future_to_sheet:
            sheet_name = future_to_sheet[future]
            try:
                inventory_results[sheet_name] = future.result()
            except Exception as e:
                print(f"⚠️ Error obteniendo datos de {sheet_name}: {e}")
                inventory_results[sheet_name] = pd.DataFrame()

    # 4. Generar y guardar Excel
    timestamp = start_time.strftime("%Y-%m-%d")
    filename = f"inventario_oci_{timestamp}.xlsx"
    file_path = os.path.join(reports_dir, filename)

    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        for sheet, df in inventory_results.items():
            df.to_excel(writer, index=False, sheet_name=sheet)

    print(f"💾 Reporte generado: {file_path}")

    # 5. Envío de correo
    handle_email_delivery(file_path, inventory_results)

    print(f"⏱️ Tiempo total de ejecución: {datetime.now() - start_time}")

if __name__ == "__main__":
    main()