# Despliegue de un Clúster Multi-Nodo Apache Hadoop con Docker

Laboratorio práctico del **Curso de Especialización en Inteligencia Artificial y Big Data (Módulo 5074/5075 · Big Data Aplicado)**, centrado en el despliegue de un clúster distribuido Apache Hadoop como código (IaC), la auditoría física de bloques en HDFS, la simulación de tolerancia a fallos ante caída de nodos y la ejecución de cómputo distribuido MapReduce sobre YARN.

---

## Arquitectura Desplegada

El entorno se construye sobre la imagen oficial `apache/hadoop:3` (Hadoop 3.3.6) orquestada mediante **Docker Compose** sobre una red puente aislada (`hadoop-net`), replicando la separación física entre nodos maestros y trabajadores:

| Servicio | Capa | Rol | Puertos |
| :--- | :--- | :--- | :--- |
| **`namenode`** | HDFS | Nodo maestro de metadatos y espacio de nombres | `9870` (Web UI) / `8020` (RPC) |
| **`datanode1`** | HDFS | Nodo trabajador de almacenamiento 1 | Interno (`9864` / `9866`) |
| **`datanode2`** | HDFS | Nodo trabajador de almacenamiento 2 | Interno (`9864` / `9866`) |
| **`datanode3`** | HDFS | Nodo trabajador de almacenamiento 3 | Interno (`9864` / `9866`) |
| **`resourcemanager`** | YARN | Planificador global de recursos de cómputo | `8088` (Web UI) / `8032` |
| **`nodemanager`** | YARN | Ejecutor de contenedores de tareas MapReduce | Interno (`8042`) |

### Parámetros clave de configuración (`docker/config`)
* **Tamaño de bloque HDFS (`dfs.blocksize`):** `67108864` bytes (`64 MiB`).
* **Factor de replicación (`dfs.replication`):** `2` réplicas físicas por bloque.
* **Gestión de memoria YARN:** Límite de `2048 MB` y `2 vCores` en el NodeManager, con asignación mínima de `256 MB` y contenedores de `512 MB` para ApplicationMaster, Map y Reduce.

---

## Estructura del Repositorio

```text
IABD-5075-LabHadoop-Moreno-Arroyo/
├── .gitignore                                      
├── README.md                                       
├── docker/
│   ├── config                                 mapred-site y yarn-site
│   └── docker-compose.yml                        
├── evidencias/
│   ├── 01_namenode_ui_9870.png                     
│   ├── 02_hdfs_fsck_bloques.png                  
│   ├── 03_simulacion_fallo_datanode2.png           
│   └── 04_yarn_wordcount_8088.png
└── informe/
    └── Moreno_Arroyo_InformeLabHadoop.pdf
```

---

## Instrucciones de Despliegue y Uso

### 1. Arrancar el clúster
Desde la raíz del repositorio, accede al directorio `docker/` y levanta los contenedores en segundo plano:

```bash
cd docker
docker compose up -d
docker compose ps
```

### 2. Interfaces web de monitorización
* **HDFS NameNode UI:** [http://localhost:9870](http://localhost:9870)
* **YARN ResourceManager UI:** [http://localhost:8088](http://localhost:8088)

### 3. Acceso al nodo maestro
Para ejecutar comandos administrativos de HDFS (`hdfs dfsadmin`, `hdfs fsck`, `hdfs dfs`) o lanzar trabajos MapReduce:

```bash
docker exec -it namenode bash
```

### 4. Apagado y limpieza del entorno
Para detener todos los servicios y eliminar los volúmenes temporales liberando los recursos del equipo anfitrión:

```bash
cd docker
docker compose down -v
```

---

## Autoría

* **Alumno:** Mario Moreno Arroyo
* **Centro:** Campus Cámara de Comercio Sevilla — Especialización en Inteligencia Artificial y Big Data (IABD)