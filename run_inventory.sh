#!/bin/bash

# Navegar a la carpeta (Usa rutas absolutas siempre en Cron)
cd /home/usuario/oci-inventory-unified

# Activar entorno virtual
source venv/bin/activate

# Imprimir separador y fecha en el log
echo "------------------------------------------" >> cron_execution.log
echo "Ejecución iniciada el: $(date)" >> cron_execution.log

# Ejecutar con el Python del entorno virtual (venv)
# Nota: Al activar el venv, basta con usar 'python'
python main.py >> cron_execution.log 2>&1

echo "Ejecución finalizada el: $(date)" >> cron_execution.log

#  cron:
# 0 8 1 * * /ruta/a/tu/repositorio/oci-inventory-unified/run_inventory.sh
# Explicación de los campos:
# 0: Minuto 0.
# 8: Hora 8 (AM).
# 1: Día del mes (el día primero).
# *: Todos los meses.
# *: Todos los días de la semana.