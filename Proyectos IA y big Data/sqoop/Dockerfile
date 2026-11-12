FROM apache/hadoop:3.4.0

USER root

# Corregir repositorios CentOS EOL e instalar JDK 8 + wget
RUN sed -i 's/^mirrorlist/#mirrorlist/g' /etc/yum.repos.d/CentOS-*.repo && \
    sed -i 's|^#\?baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' /etc/yum.repos.d/CentOS-*.repo && \
    yum clean all && \
    yum install -y java-1.8.0-openjdk-devel wget && \
    yum clean all

ENV JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk
ENV PATH=$JAVA_HOME/bin:$PATH

# Descargar e instalar Sqoop 1.4.7
RUN wget https://archive.apache.org/dist/sqoop/1.4.7/sqoop-1.4.7.bin__hadoop-2.6.0.tar.gz \
    && tar -xvf sqoop-1.4.7.bin__hadoop-2.6.0.tar.gz -C /opt/ \
    && mv /opt/sqoop-1.4.7.bin__hadoop-2.6.0 /opt/sqoop \
    && rm sqoop-1.4.7.bin__hadoop-2.6.0.tar.gz

# Descargar e instalar Apache Flume 1.11.0
RUN wget https://archive.apache.org/dist/flume/1.11.0/apache-flume-1.11.0-bin.tar.gz \
    && tar -xvf apache-flume-1.11.0-bin.tar.gz -C /opt/ \
    && mv /opt/apache-flume-1.11.0-bin /opt/flume \
    && rm apache-flume-1.11.0-bin.tar.gz

# Descargar el conector JDBC de MySQL
RUN wget https://repo1.maven.org/maven2/mysql/mysql-connector-java/8.0.28/mysql-connector-java-8.0.28.jar \
    -O /opt/sqoop/lib/mysql-connector-java-8.0.28.jar

# Configuración de variables de entorno (Sqoop + Flume + Hadoop)
ENV SQOOP_HOME=/opt/sqoop
ENV FLUME_HOME=/opt/flume
ENV HADOOP_HOME=/opt/hadoop
ENV PATH=$PATH:$SQOOP_HOME/bin:$FLUME_HOME/bin
ENV HADOOP_CLASSPATH=.

WORKDIR /opt/sqoop

CMD ["tail", "-f", "/dev/null"]