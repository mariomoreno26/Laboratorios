FROM continuumio/anaconda3:2024.02-1

RUN conda install -y -c conda-forge openjdk=17 \
    && conda clean -afy

ENV PYSPARK_PYTHON=/opt/conda/bin/python
ENV PYSPARK_DRIVER_PYTHON=/opt/conda/bin/python

RUN pip install --no-cache-dir \
        pyspark==3.5.0 kafka-python pymongo psycopg2-binary sqlalchemy hdfs pyarrow

WORKDIR /workspace
EXPOSE 8888

CMD ["bash", "-c", "jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --ServerApp.token=${JUPYTER_TOKEN} --notebook-dir=/workspace"]