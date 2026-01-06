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

def format_size(bytes_val):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024: return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.2f} PB"

def get_buckets(config, compartments):
    print("\n🔄 Obteniendo Buckets de Object Storage...")
    os_client = oci.object_storage.ObjectStorageClient(config)
    
    try:
        namespace = os_client.get_namespace().data
    except Exception as e:
        print(f"  ❌ Error obteniendo namespace: {e}")
        return pd.DataFrame()

    all_buckets_data = []

    def process_bucket(bucket_summary, comp_name):
        try:
            # Print sutil para buckets grandes
            # print(f"    📦 Procesando objetos de: {bucket_summary.name}...")
            total_size = 0
            obj_count = 0
            next_start = None
            
            while True:
                res = os_client.list_objects(
                    namespace, bucket_summary.name, 
                    fields="name,size", limit=1000, start=next_start
                ).data
                for obj in res.objects:
                    total_size += (obj.size if obj.size else 0)
                    obj_count += 1
                next_start = res.next_start_with
                if not next_start: break
            
            return {
                'compartment_name': comp_name,
                'bucket_name': bucket_summary.name,
                'objects': obj_count,
                'size': format_size(total_size)
            }
        except Exception as e:
            print(f"    ⚠️ Error en bucket {bucket_summary.name}: {e}")
            return None

    # 1. Listar Buckets
    buckets_to_process = []
    for comp in compartments:
        try:
            bs = oci.pagination.list_call_get_all_results(
                os_client.list_buckets, namespace, comp.id
            ).data
            if bs:
                for b in bs: 
                    buckets_to_process.append((b, comp.name))
        except Exception:
            continue

    # 2. Procesar detalles en paralelo
    if not buckets_to_process:
        return pd.DataFrame(columns=['compartment_name', 'bucket_name', 'objects', 'size'])


    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(lambda p: process_bucket(*p), buckets_to_process))
    
    final_data = [r for r in results if r]
    print(f" ✅ Buckets: {len(final_data)} procesados exitosamente.")
    
    return pd.DataFrame(final_data)