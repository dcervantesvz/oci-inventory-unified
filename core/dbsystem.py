# -*- coding: utf-8 -*-
"""
Nombre del Proyecto: oci-inventory-unified
Autor: Daniel de Jesús Cervantes Velázquez
Equipo: Automatización OCI
Licencia: MIT
"""
import oci
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

def get_db_systems(config, compartments):
    """
    Obtiene todos los DB Systems usando procesamiento paralelo por compartimento.
    """
    print("\n🚀 Iniciando obtención de DB Systems (Modo Paralelo)...")

    # Clientes OCI
    database_client = oci.database.DatabaseClient(config)
    network_client = oci.core.VirtualNetworkClient(config)

    def get_ip_details(ip_ids):
        """Helper para obtener detalles de IPs privadas en paralelo si fuera necesario, 
        aunque aquí lo mantenemos simple pero controlado."""
        ips = []
        for ip_id in ip_ids:
            try:
                private_ip = network_client.get_private_ip(ip_id).data
                ips.append(f"{private_ip.ip_address} ({private_ip.display_name})")
            except: continue
        return ", ".join(ips) if ips else "N/A"

    def process_compartment(compartment):
        comp_db_data = []
        try:
            # Listar DB Systems del compartimento
            db_systems = oci.pagination.list_call_get_all_results(
                database_client.list_db_systems,
                compartment_id=compartment.id
            ).data

            for db_sys in db_systems:
                # Filtrar estados no deseados
                if db_sys.lifecycle_state in ["TERMINATED", "TERMINATING", "FAILED"]:
                    continue

                # Lógica de OCPUs mejorada
                shape = db_sys.shape
                cpu_count = db_sys.cpu_core_count
                
                # Deducción de OCPUs para shapes fijos (ej. BM.Standard2.52 -> 52)
                shape_ocpus = cpu_count
                if ".Flex" not in shape:
                    parts = shape.split('.')
                    if parts[-1].isdigit():
                        shape_ocpus = int(parts[-1])

                # Obtener IPs (SCAN y VIP)
                formatted_scan = get_ip_details(db_sys.scan_ip_ids) if db_sys.scan_ip_ids else "N/A"
                formatted_vip = get_ip_details(db_sys.vip_ids) if db_sys.vip_ids else "N/A"

                comp_db_data.append({
                    'compartment_name': compartment.name,
                    'name': db_sys.display_name,
                    'shape': shape,
                    'cpu_core_count': cpu_count,
                    'db_storage_gb': db_sys.data_storage_size_in_gbs,
                    'shape_ocpus': shape_ocpus,
                    'memory_gb': db_sys.memory_size_in_gbs or 0,
                    'local_storage_tb': round(db_sys.data_storage_size_in_gbs / 1024, 2),
                    'node_count': db_sys.node_count,
                    'license_model': db_sys.license_model.replace("LICENSE_", "").replace("_", " "),
                    'scan_ips': formatted_scan,
                    'vip_ips': formatted_vip,
                    'db_home_version': db_sys.version,
                    'status': db_sys.lifecycle_state
                })
        except Exception as e:
            if "Authorization failed" not in str(e):
                print(f" ⚠️ Error en compartimento {compartment.name}: {e}")
        
        return comp_db_data

    # Ejecución paralela por compartimento
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(process_compartment, compartments))

    # Aplanar resultados
    db_data = [item for sublist in results for item in sublist]

    columns = [
        'compartment_name', 'name', 'shape', 'cpu_core_count',
        'db_storage_gb', 'shape_ocpus', 'memory_gb', 'local_storage_tb',
        'node_count', 'license_model', 'scan_ips', 'vip_ips', 'db_home_version', 'status'
    ]
    
    df = pd.DataFrame(db_data) if db_data else pd.DataFrame(columns=columns)
    print(f" ✅ DB Systems: {len(db_data)} sistemas procesados.")
    return df