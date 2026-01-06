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

def get_oic_instances(config, compartments):
    print("\n🚀 Iniciando obtención de Oracle Integration (OIC)...")
    oic_client = oci.integration.IntegrationInstanceClient(config)

    def process_compartment(compartment):
        comp_oic_data = []
        try:
            instances = oci.pagination.list_call_get_all_results(
                oic_client.list_integration_instances, compartment_id=compartment.id
            ).data

            for oic in instances:
                if oic.lifecycle_state in ["DELETED", "DELETING"]:
                    continue

                comp_oic_data.append({
                    'compartment_name': compartment.name,
                    'name': oic.display_name,
                    'instance_url': oic.instance_url or "N/A",
                    'message_packs': oic.message_packs,
                    'licensing': "BYOL" if oic.is_byol else "License Included",
                    'status': oic.lifecycle_state
                })
        except Exception:
            pass
        return comp_oic_data

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(process_compartment, compartments))

    flat_results = [item for sublist in results for item in sublist]
    print(f" ✅ OIC: {len(flat_results)} instancias encontradas.")
    return pd.DataFrame(flat_results) if flat_results else pd.DataFrame(columns=['compartment_name', 'name', 'instance_url', 'message_packs', 'licensing'])