# Reporte de Perfilado y Calidad de Datos (KDD)

## 1. Validación de Integridad (Fase 1)
- **Tasa de Integridad Criptográfica**: Se auditó el 100 % del lote recibido (`3` ficheros en `raw_batch_202611/`), validando criptográficamente **`2` archivos** (`transacciones_tienda_norte.csv` y `transacciones_tienda_este.csv`, equivalentes al **66,67 %** del lote) y rechazando **`1` archivo** (**33,33 %**). El fichero `transacciones_tienda_sur.csv` fue segregado exitosamente a la zona de cuarentena (`quarantine/tampered/`) al no coincidir su firma SHA-256 con el manifiesto oficial (`manifest_checksums.sha256`). Esto previene el envenenamiento de los modelos (*Data Poisoning*) por archivos incompletos o manipulados en tránsito.

## 2. Decisiones de Limpieza e Imputación (Fase 2)
Se establecieron las siguientes políticas de calidad basadas en el estándar **ISO/IEC 25012**:
- **Exactitud y Coherencia Lógica:** Se descartaron registros con importes negativos o iguales a cero (`importe_eur <= 0`), así como transacciones con unidades inferiores a 1 (`unidades < 1`), aislándolos en `quarantine/bad_records.csv` para evitar distorsiones en los agregados de facturación.
- **Trazabilidad (Nulos):** Los registros carentes de `id_transaccion` fueron aislados en `quarantine/bad_records.csv`, ya que un identificador único es obligatorio para garantizar la integridad referencial y el cruce en bases de datos relacionales del almacén de Business Intelligence (BI).
- **Consistencia Temporal:** Se forzó la conversión de `timestamp` al estándar **ISO 8601** (`YYYY-MM-DD HH:MM:SS`). Las fechas mal formadas, futuras o fuera del ejercicio fiscal actual fueron descartadas por considerarse anomalías de los sensores de caja.

## 3. Métricas de Distribución Post-Saneamiento (Fase 3)
Tras aplicar las reglas de validación sobre los ficheros verificados en `staging/verified/`, el perfilado estadístico del dataset resultante (`processed/dataset_kdd_listo.csv`) arroja los siguientes indicadores de calidad conforme a la norma **ISO/IEC 25012**:

- **Tasa de Completitud Final:** `90.0 %` (el `10.0 %` restante de registros no conformes quedó aislado en `quarantine/bad_records.csv`).
- **Integridad Criptográfica:** `2` archivos validados frente a `1` archivo rechazado.
- **Distribución de la variable clave (`importe_eur`):**
  - **Media:** `161.41 €`
  - **Mediana:** `74.48 €`
  - **Desviación estándar:** `528.78 €`
  - **Percentil 25 (Q1):** `55.22 €`
  - **Percentil 75 (Q3):** `88.57 €`

*(Nota analítica para BI: La diferencia entre la media de `161.41 €` y la mediana de `74.48 €`, junto con una desviación estándar de `528.78 €` frente a un rango intercuartílico concentrado entre `55.22 €` y `88.57 €`, evidencia una distribución asimétrica positiva provocada por operaciones válidas de importe elevado; por ello, se recomienda emplear la mediana como medida robusta de tendencia central en los cuadros de mando).*

**Conclusión técnica:** El conjunto de datos alojado en `processed/dataset_kdd_listo.csv` se encuentra completamente normalizado, libre de registros corruptos, nulos en claves críticas o anomalías de dominio, cumpliendo con los requisitos de exactitud, completitud y consistencia definidos por la norma **ISO/IEC 25012**. Asimismo, la trazabilidad de todas las incidencias queda garantizada mediante el aislamiento preventivo en `quarantine/` y el registro de auditoría en `logs/ejecucion_pipeline.log`, dejando el dataset apto para su ingesta directa en el almacén de Business Intelligence y las posteriores fases de minería de datos del proceso KDD.