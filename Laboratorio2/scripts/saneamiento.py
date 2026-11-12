import hashlib
import pandas as pd


def calcular_sha256(ruta_archivo):
  sha = hashlib.sha256()
  with open(ruta_archivo, 'rb') as f:
    for bloque in iter(lambda: f.read(4096), b''):
      sha.update(bloque)
  return sha.hexdigest()


# Rutas de entrada y salida
fichero_origen = 'datos/telemetria_envios.csv'
fichero_destino = 'datos/telemetria_limpia.csv'

# 1. Hash original
hash_inicial = calcular_sha256(fichero_origen)
print(f'Hash SHA-256 Original: {hash_inicial}')

# 2. Carga del conjunto de datos
df = pd.read_csv(fichero_origen)
registros_iniciales = len(df)

# 3. Limpieza y depuración
# a) Eliminación de filas duplicadas
df = df.drop_duplicates()

# b) Eliminación de nulos en campos críticos
df = df.dropna(subset=['temp_celsius', 'peso_kg', 'destino'])

# c) Filtrado de rangos inconsistentes
df = df[df['peso_kg'] >= 0]
df = df[df['temp_celsius'] <= 50.0]
df = df[df['estado_envio'] != 'DESCONOCIDO_ERROR']

# 4. Exportación del fichero limpio
df.to_csv(fichero_destino, index=False)
registros_finales = len(df)

# 5. Hash depurado
hash_final = calcular_sha256(fichero_destino)
print(f'Hash SHA-256 Limpio:   {hash_final}')
print(f'Filas procesadas: {registros_iniciales} -> {registros_finales}')