#!/bin/bash
# Arranca HDFS + YARN en modo pseudodistribuido dentro de un único contenedor.
# No requiere SSH: los demonios se lanzan directamente con --daemon start.

#Obliga a que el script falle si algún comando falla, si se usan variables no definidas o si un comando en un pipe falla
set -euo pipefail

HADOOP_HOME="${HADOOP_HOME:-/opt/hadoop}"
export PATH="$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$PATH"

# Formatear el NameNode solo la primera vez (el volumen hdfs-data persiste)
if [ ! -d /hadoop/dfs/name/current ]; then
  echo ">>> Formateando NameNode (primer arranque)..."
  hdfs namenode -format -force -nonInteractive
fi

stop_all() {
  echo ">>> Deteniendo daemons..."
  yarn --daemon stop nodemanager      || true
  yarn --daemon stop resourcemanager  || true
  hdfs --daemon stop datanode         || true
  hdfs --daemon stop namenode         || true
  exit 0
}
#manejo de apagado controlado para que los daemons se detengan correctamente
trap stop_all SIGTERM SIGINT

#Depliega los daemons de Hadoop en el contenedor
echo ">>> Arrancando HDFS..."
hdfs --daemon start namenode
hdfs --daemon start datanode

echo ">>> Arrancando YARN..."
yarn --daemon start resourcemanager
yarn --daemon start nodemanager

echo ">>> Esperando a que HDFS salga del modo seguro..."
hdfs dfsadmin -safemode wait || true

echo ">>> Demonios activos (jps):"
jps

echo ">>> Listo. NameNode UI: http://localhost:9870 | YARN UI: http://localhost:8088"

# Mantener el contenedor vivo mostrando los logs
tail -F -n 0 "$HADOOP_HOME"/logs/*.log &
wait $!
