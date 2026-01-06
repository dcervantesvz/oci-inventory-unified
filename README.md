# OCI Unified Inventory Automation 🚀

Herramienta automatizada en Python para la generación de inventarios técnicos detallados en **Oracle Cloud Infrastructure (OCI)**. El sistema extrae datos de múltiples servicios, consolida la información en un reporte Excel multihidra y lo distribuye automáticamente vía SMTP.

## 🌟 Características Principales

- **Ejecución Paralela:** Utiliza `ThreadPoolExecutor` para consultar servicios simultáneamente, reduciendo drásticamente el tiempo de espera.
- **Reporte Unificado:** Genera un archivo `.xlsx` con pestañas dedicadas para:
  - Compute (Instancias y VNICs)
  - Base de Datos (DB Systems)
  - Object Storage (Buckets y conteo de objetos)
  - Integración (OIC Instances)
  - Load Balancers
  - File Storage (Uso de disco mediante métricas)
- **Notificación Automática:** Envío del reporte por correo electrónico a través de OCI Email Delivery.
- **Estructura Modular:** Código organizado en paquetes (`core/` y `utils/`) para fácil mantenimiento.

### 📊 Detalle de los Reportes por Servicio

El inventario genera una pestaña por cada servicio de OCI con los siguientes campos técnicos:

| Servicio              | Campos Extraídos                                                                                                                            |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| **Compute**           | Nombre de instancia, Estado (Running/Stopped), Compartimento, IP Privada, IP Pública, Shape (OCPUs/Memoria), Imagen/OS y Fecha de creación. |
| **Base de Datos**     | Nombre del DB System, Versión de la base de datos, Estado, Forma (Shape), Almacenamiento total (GB), Compartimento y Nodo.                  |
| **Object Storage**    | Nombre del Bucket, Namespace, Número total de objetos, Tamaño total (formateado en KB/MB/GB) y Nombre del compartimento.                    |
| **OIC (Integration)** | Nombre de la instancia, Edición (Standard/Enterprise), Estado, Tipo de mensaje, Capacidad (Message Packs) y OCID.                           |
| **Load Balancers**    | Nombre del LB, Estado (Active/Failed), Tipo (Public/Private), Ancho de banda (Mbps), Dirección IP y Listener port.                          |
| **File Storage**      | Nombre del sistema de archivos (File System), Tamaño utilizado (Métricas), Punto de montaje y Compartimento.                                |

## 📂 Estructura del Proyecto

```text
.
├── core/                # Lógica de extracción por servicio
├── utils/               # Funciones auxiliares (Mailer, etc.)
├── reports/             # Carpeta de salida de reportes (Auto-generada)
├── config.ini           # Configuración SMTP (No incluir en el repo)
├── main.py              # Orquestador principal
├── requirements.sh      # Dependencias del proyecto
└── run_inventory.txt    # Ejecutable para usar en cron y un environment

```

## 🛠️ Instalación y Configuración

### 1. Requisitos Previos

- Python 3.8 o superior.
- Credenciales de OCI configuradas en `~/.oci/config`.
- Credenciales SMTP generadas en la consola de OCI (User Settings -> SMTP Credentials).

### 2. Clonar e Instalar

```bash
git clone [https://github.com/tu-usuario/nombre-repo.git](https://github.com/tu-usuario/nombre-repo.git)
cd nombre-repo
pip install -r requirements.txt

```

### 3. Configurar Credenciales

Crea un archivo `config.ini` en la raíz con el siguiente formato:

```ini
[SMTP]
host = smtp.email.us-ashburn-1.oci.oraclecloud.com
port = 587
user = ocid1.user.oc1..tu_usuario_smtp
password = tu_password_smtp
sender = reporte@tu-dominio.com
receiver = operadores@tu-dominio.com
subject = Inventario Unificado OCI

```

## 🚀 Uso

Para iniciar el escaneo y envío del reporte, simplemente ejecuta:

```bash
python main.py

```

## 📧 Formato del Mensaje

El equipo de operadores recibirá un correo con el siguiente cuerpo:

> "Este reporte incluye información relevante para las tareas de monitoreo y control de la infraestructura en OCI..."

## 👥 Autores

- **[Tu Nombre]** - _Desarrollo Principal_ - [Daniel de Jesús Cervantes Velázquez]
- **Equipo de Automatización OCI** - _Mantenimiento y Soporte_
