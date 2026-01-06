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

def get_file_systems(config, compartments):
    """
    Obtiene File Systems y su tamaño utilizado mediante procesamiento paralelo.
    """
    print("\n🚀 Iniciando obtención de File Storage (FSS) con métricas paralelas...")

    fss_client = oci.file_storage.FileStorageClient(config)
    monitoring_client = oci.monitoring.MonitoringClient(config)
    
    namespace = "oci_os"
    fss_results = []

    def get_fs_usage(fs_id, compartment_id):
        """Consulta el tamaño utilizado en el servicio de Monitoring."""
        try:
            query = f"UsedBytes[1m].mean().by(resourceId).where(resourceId='{fs_id}')"
            metric_data = monitoring_client.summarize_metrics_data(
                compartment_id=compartment_id,
                summarize_metrics_data_details=oci.monitoring.models.SummarizeMetricsDataDetails(
                    namespace=namespace,
                    query=query
                )
            ).data

            if metric_data and metric_data[0].aggregated_datapoints:
                # Obtenemos el último punto de datos
                used_bytes = metric_data[0].aggregated_datapoints[-1].value
                return round(used_bytes / (1024 ** 3), 2)
            return 0.0
        except:
            return "N/A"

    def process_compartment(compartment):
        comp_data = []
        try:
            # Listar todos los FS del compartimento (Regional + Zonal)
            file_systems = oci.pagination.list_call_get_all_results(
                fss_client.list_file_systems,
                compartment_id=compartment.id,
                availability_domain=None
            ).data


            for fs in file_systems:
                # if fs.lifecycle_state != "ACTIVE":
                #     continue

                # Consultar uso (esta es la parte lenta que ahora corre en hilos)
                size_gb = round(fs.metered_bytes / (1024 ** 3), 1)

                comp_data.append({
                    'compartment_name': compartment.name,
                    'display_name': fs.display_name,
                    'size_gb': size_gb,
                    'status': fs.lifecycle_state
                })
        except Exception:
            pass
        return comp_data

    # Ejecución paralela por compartimento
    # Usamos max_workers=10 para manejar múltiples llamadas a Monitoring simultáneas
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(process_compartment, compartments))

    # Aplanar la lista de resultados
    fss_results = [item for sublist in results for item in sublist]
    
    columns = ['compartment_name', 'display_name', 'size_gb', 'status']
    df = pd.DataFrame(fss_results) if fss_results else pd.DataFrame(columns=columns)
    
    print(f" ✅ File Systems: {len(fss_results)} procesados.")
    return df