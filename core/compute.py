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

def get_compute_instances(config, compartments):
    print("\n🚀 Iniciando obtención de instancias (Optimización Masiva)...")

    compute_client = oci.core.ComputeClient(config)
    network_client = oci.core.VirtualNetworkClient(config)
    block_storage_client = oci.core.BlockstorageClient(config)

    image_cache = {}

    def process_compartment(compartment):
        """Procesa un compartimento completo de forma más eficiente."""
        comp_instances_data = []
        try:
            # 1. Obtener todas las instancias del compartimento
            instances = oci.pagination.list_call_get_all_results(
                compute_client.list_instances, compartment_id=compartment.id
            ).data
            
            if not instances:
                return []

            # 2. Pre-cargar mapeos masivos para evitar llamadas individuales por instancia
            # Mapeo de VNIC attachments: {instance_id: [vnic_id1, ...]}
            vnic_attachments = oci.pagination.list_call_get_all_results(
                compute_client.list_vnic_attachments, compartment_id=compartment.id
            ).data
            vnic_map = {}
            for va in vnic_attachments:
                if va.lifecycle_state == "ATTACHED":
                    vnic_map[va.instance_id] = va.vnic_id

            # 3. Procesar cada instancia usando los datos pre-cargados
            for inst in instances:
                if inst.lifecycle_state in ["TERMINATED", "TERMINATING"]:
                    continue

                # --- IPs (Solo si tenemos el ID en el mapa) ---
                pub_ip, priv_ip = "N/A", "N/A"
                vnic_id = vnic_map.get(inst.id)
                if vnic_id:
                    try:
                        vnic = network_client.get_vnic(vnic_id).data
                        pub_ip = vnic.public_ip or "N/A"
                        priv_ip = vnic.private_ip or "N/A"
                    except: pass

                # --- Info de Imagen (Caché) ---
                img_name, os_type = "N/A", "N/A"
                if inst.image_id:
                    if inst.image_id not in image_cache:
                        try:
                            img = compute_client.get_image(inst.image_id).data
                            image_cache[inst.image_id] = (img.display_name, img.operating_system)
                        except: image_cache[inst.image_id] = ("Custom/Private", "N/A")
                    img_name, os_type = image_cache[inst.image_id]

                # --- Almacenamiento (Se mantiene individual por AD/ID) ---
                boot_size = 0
                try:
                    ba = compute_client.list_boot_volume_attachments(
                        availability_domain=inst.availability_domain,
                        compartment_id=inst.compartment_id, instance_id=inst.id
                    ).data
                    if ba:
                        boot_size = block_storage_client.get_boot_volume(ba[0].boot_volume_id).data.size_in_gbs
                except: pass

                block_total = 0
                try:
                    vas = compute_client.list_volume_attachments(
                        availability_domain=inst.availability_domain,
                        compartment_id=inst.compartment_id, instance_id=inst.id
                    ).data
                    for a in vas:
                        block_total += block_storage_client.get_volume(a.volume_id).data.size_in_gbs
                except: pass

                comp_instances_data.append({
                    'compartment_name': compartment.name,
                    'server_name': inst.display_name,
                    'Type': os_type,
                    'image': img_name,
                    'shape': inst.shape,
                    'ocpus': inst.shape_config.ocpus if inst.shape_config else "N/A",
                    'memory_gb': inst.shape_config.memory_in_gbs if inst.shape_config else "N/A",
                    'public_ips': pub_ip,
                    'private_ips': priv_ip,
                    'boot_volume_size_gb': boot_size,
                    'block_volumes_total_gb': block_total,
                    'status': inst.lifecycle_state
                })
        except Exception as e:
            print(f"⚠️ Error en compartimento {compartment.name}: {e}")
        
        return comp_instances_data

    # Ejecución paralela por COMPARTIMENTO
    # Es mejor paralelizar por compartimento que por instancia para no saturar los límites de la API
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(process_compartment, compartments))

    # Aplanar lista de listas
    flat_results = [item for sublist in results for item in sublist]
    print(f"✅ Proceso completado. {len(flat_results)} instancias encontradas.")
    
    return pd.DataFrame(flat_results)