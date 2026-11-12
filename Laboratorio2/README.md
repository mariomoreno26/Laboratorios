# Práctica Integradora: Consolidación de Almacenamiento, Integridad del Dato y HDFS

## Información General
- **Entorno:** Docker (Apache Hadoop 3.4.0 en modo pseudodistribuido)
- **Dataset:** Telemetría logística de envíos (`telemetria_envios.csv`)

---

## Sección 1: Integridad y Depuración del Dato (Módulo 5075)

Para garantizar la trazabilidad y calidad de la información antes de su ingesta distribuida, se aplicó un proceso de saneamiento en Python eliminando duplicados, nulos en campos clave y lecturas inconsistentes (pesos negativos, temperaturas superiores a 50°C y estados con error).

### Registro de Huellas Criptográficas (SHA-256)
| Estado del Fichero | Fichero | Hash SHA-256 |
| :--- | :--- | :--- |
| **Original (en bruto)** | `datos/telemetria_envios.csv` | `4471c18a0284b3aa5b32a0713e691e3c7fcadae402f105e901c7c57f49474911` |
| **Saneado (limpio)** | `datos/telemetria_limpia.csv` | `23fe3d0b4801e8d90fe7bd79004f79c74058fa79c6de0a62d0964ce616f42513` |

> **Nota:** La modificación del hash evidencia el efecto avalancha de las funciones SHA-256 ante cualquier variación en el contenido del archivo.

---

## Sección 2: Despliegue e Ingesta en HDFS (Módulo 5074)

### 1. Despliegue del Contenedor
El entorno se desplegó mediante Docker Compose utilizando la imagen `apache/hadoop:3.4.0` con el puerto `9870` mapeado para la interfaz Web UI del NameNode y el puerto `8088` para YARN ResourceManager.

### 2. Comprobación de Servicios Java
Dentro del contenedor se verificó la ejecución de los daemons principales mediante el comando `jps`:
- **NameNode:** Administrador del espacio de nombres de HDFS y metadatos.
- **DataNode:** Almacenamiento físico de los bloques de datos.
- **ResourceManager:** Gestor global de recursos de YARN.
- **NodeManager:** Agente local de ejecución en el nodo.

### 3. Comandos HDFS Ejecutados
```bash
# Crear estructura distribuida
hdfs dfs -mkdir -p /empresa/logistica/input

# Ingestar archivo saneado
hdfs dfs -put /workspace/telemetria_limpia.csv /empresa/logistica/input/

# Listar contenido
hdfs dfs -ls /empresa/logistica/input/

# Auditar bloques físicos
hdfs fsck /empresa/logistica/input/telemetria_limpia.csv -files -blocks -locations