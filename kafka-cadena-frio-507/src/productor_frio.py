import json
import time
import random
from datetime import datetime, timezone
from confluent_kafka import Producer

conf = {
    'bootstrap.servers': 'localhost:9092',
    'acks': 'all'
}
producer = Producer(conf)

TOPIC = 'telemetria-frio'
VEHICULOS = ["CAM-01", "CAM-02", "CAM-03", "CAM-04"]
TOTAL_EVENTOS = 60

indices_anomalias = set(random.sample(range(TOTAL_EVENTOS), k=8))
anomalias_emitidas = 0

def confirmacion_entrega(err, msg):
    if err is not None:
        print(f"Error al entregar mensaje: {err}")
    else:
        print(f"Confirmado -> Partición: {msg.partition()} | Offset: {msg.offset()}")

for i in range(TOTAL_EVENTOS):
    vehiculo = random.choice(VEHICULOS)
    
    if i in indices_anomalias:
        temp = round(random.uniform(-17.5, -14.0), 1)
        anomalias_emitidas += 1
    else:
        temp = round(random.uniform(-22.0, -18.5), 1)

    evento = {
        "vehiculo": vehiculo,
        "temp_c": temp,
        "lat": round(random.uniform(37.35, 37.42), 4),
        "lon": round(random.uniform(-6.01, -5.95), 4),
        "timestamp iso": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    }

    print(f"[{i+1}/{TOTAL_EVENTOS}] Enviando {vehiculo} ({temp}°C)...", end=" ")
    
    producer.produce(
        TOPIC,
        key=vehiculo.encode('utf-8'),
        value=json.dumps(evento).encode('utf-8'),
        on_delivery=confirmacion_entrega
    )
    producer.poll(0)
    time.sleep(0.5)

producer.flush()
print(f"\nResumen: Total de anomalías emitidas = {anomalias_emitidas}")