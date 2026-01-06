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

def get_load_balancers(config, compartments):
    print("\n🚀 Iniciando obtención de Load Balancers (Modo Paralelo)...")
    lb_client = oci.load_balancer.LoadBalancerClient(config)

    def process_compartment(compartment):
        comp_lb_data = []
        try:
            # Listar LBs del compartimento
            lbs = oci.pagination.list_call_get_all_results(
                lb_client.list_load_balancers, compartment_id=compartment.id
            ).data

            for lb in lbs:
                if lb.lifecycle_state in ["TERMINATING", "DELETED"]:
                    continue

                shape = lb.shape_name
                # Si es flexible, necesitamos una llamada extra para ver los Mbps
                if shape.lower() == "flex":
                    try:
                        # get_load_balancer es costoso, pero necesario para el config flex
                        details = lb_client.get_load_balancer(lb.id).data
                        if details.shape_details:
                            shape = f"flex ({details.shape_details.minimum_bandwidth_in_mbps}-{details.shape_details.maximum_bandwidth_in_mbps} Mbps)"
                    except: pass

                # Procesar IPs
                ips = []
                for ip_obj in lb.ip_addresses:
                    tipo = "Pública" if ip_obj.is_public else "Privada"
                    ips.append(f"{ip_obj.ip_address} ({tipo})")

                comp_lb_data.append({
                    'compartment_name': compartment.name,
                    'name': lb.display_name,
                    'shape': shape,
                    'ip_addresses': ", ".join(ips) if ips else "N/A",
                    'status': lb.lifecycle_state
                })
        except Exception:
            pass # Errores de permisos comunes en LBs se ignoran silenciosamente
        return comp_lb_data

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(process_compartment, compartments))

    flat_results = [item for sublist in results for item in sublist]
    print(f" ✅ Load Balancers: {len(flat_results)} encontrados.")
    return pd.DataFrame(flat_results) if flat_results else pd.DataFrame(columns=['compartment_name', 'name', 'shape', 'ip_addresses', 'status'])