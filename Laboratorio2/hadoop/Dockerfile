FROM apache/hadoop:3.4.0

USER root

# Directorios de datos de HDFS, logs y espacio de trabajo
RUN mkdir -p /hadoop/dfs/name /hadoop/dfs/data /workspace /opt/hadoop/logs \
    && chown -R hadoop:hadoop /hadoop /workspace /opt/hadoop/logs

# Configuración pseudodistribuida
COPY --chown=hadoop:hadoop conf/core-site.xml   /opt/hadoop/etc/hadoop/core-site.xml
COPY --chown=hadoop:hadoop conf/hdfs-site.xml   /opt/hadoop/etc/hadoop/hdfs-site.xml
COPY --chown=hadoop:hadoop conf/mapred-site.xml /opt/hadoop/etc/hadoop/mapred-site.xml
COPY --chown=hadoop:hadoop conf/yarn-site.xml   /opt/hadoop/etc/hadoop/yarn-site.xml

COPY --chmod=755 entrypoint.sh /entrypoint.sh
COPY --chmod=755 jps /usr/local/bin/jps
RUN sed -i 's/\r$//' /entrypoint.sh /usr/local/bin/jps

USER hadoop
WORKDIR /workspace

EXPOSE 9870 8088 9864 9000

ENTRYPOINT ["/entrypoint.sh"]
