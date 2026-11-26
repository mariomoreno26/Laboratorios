import json
import os
from confluent_kafka import Consumer

os.makedirs("evidencias", exist_ok=True)
RUTA_LOG = "evidencias/alertas_detectadas.log"

conf = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'grupo-alertas-frio',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': False
}

consumer = Consumer(conf)
consumer.subscribe(['telemetria-frio'])

print("Escuchando telemetría de frío... (Pulsa Ctrl+C para detener)")

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"Error del consumidor: {msg.error()}")
            continue

        vehiculo = msg.key().decode('utf-8') if msg.key() else None
        datos = json.loads(msg.value().decode('utf-8'))
        temp = datos["temp_c"]

        print(f"[Partición {msg.partition()} | Offset {msg.offset()}] Vehículo: {vehiculo} | Temp: {temp}°C")

        if temp > -18.0:
            print(f"ALERTA: Rotura de cadena de frío en {vehiculo}: {temp}°C")
            with open(RUTA_LOG, mode="a", encoding="utf-8") as f:
                f.write(f"ALERTA | Partición: {msg.partition()} | Offset: {msg.offset()} | Datos: {json.dumps(datos)}\n")
                f.flush()

        consumer.commit(asynchronous=False)

except KeyboardInterrupt:
    print("\nConsumidor detenido manualmente.")
finally:
    consumer.close()