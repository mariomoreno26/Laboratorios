import pandas as pd
import numpy as np
import json
import logging
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "ejecucion_pipeline.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

def ejecutar_pipeline_saneamiento():
    staging_dir = BASE_DIR / "staging" / "verified"
    processed_dir = BASE_DIR / "processed"
    quarantine_dir = BASE_DIR / "quarantine"
    output_dir = BASE_DIR / "output_samples"

    processed_dir.mkdir(parents=True, exist_ok=True)
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    archivos_csv = list(staging_dir.glob("*.csv"))
    if not archivos_csv:
        msg = "No hay archivos verificados en staging/verified/. Ejecuta primero 01_verificar_integridad.py."
        logging.error(msg)
        print(f"[ERROR] {msg}")
        return

    # 1. Carga y concatenación
    df_list = [pd.read_csv(f) for f in archivos_csv]
    df = pd.concat(df_list, ignore_index=True)
    total_registros_iniciales = len(df)
    logging.info(f"Dataset cargado. Registros iniciales: {total_registros_iniciales}")

    # 2. Gestión de Nulos (segregar transacciones sin ID)
    mascara_sin_id = df["id_transaccion"].isnull()
    df_malos = df[mascara_sin_id].copy()
    df_validos = df[~mascara_sin_id].copy()

    # 3. Coherencia Temporal (ISO 8601) y filtrado de años anómalos
    df_validos["timestamp"] = pd.to_datetime(df_validos["timestamp"], errors="coerce")
    anyo_actual = datetime.now().year

    mascara_fecha_invalida = (
        df_validos["timestamp"].isnull()
        | (df_validos["timestamp"].dt.year > anyo_actual)
        | (df_validos["timestamp"].dt.year < anyo_actual)
    )
    df_malos = pd.concat([df_malos, df_validos[mascara_fecha_invalida]], ignore_index=True)
    df_validos = df_validos[~mascara_fecha_invalida].copy()

    # 4. Reglas de Dominio (importe_eur > 0, unidades >= 1)
    df_validos["importe_eur"] = pd.to_numeric(df_validos["importe_eur"], errors="coerce")
    df_validos["unidades"] = pd.to_numeric(df_validos["unidades"], errors="coerce")

    mascara_dominio = (df_validos["importe_eur"] > 0) & (df_validos["unidades"] >= 1)
    df_malos = pd.concat([df_malos, df_validos[~mascara_dominio]], ignore_index=True)
    df_validos = df_validos[mascara_dominio].copy()

    # 5. Exportación
    df_malos.to_csv(quarantine_dir / "bad_records.csv", index=False)
    df_validos.to_csv(processed_dir / "dataset_kdd_listo.csv", index=False)
    logging.info(
        f"Limpieza finalizada. Registros válidos: {len(df_validos)}, Registros en cuarentena: {len(df_malos)}"
    )

    # 6. Generación de Métricas de Perfilado (ISO/IEC 25012)
    tasa_completitud = (len(df_validos) / total_registros_iniciales) * 100 if total_registros_iniciales else 0.0

    archivos_validados, archivos_rechazados = 0, 0
    manifest_txt = output_dir / "quarantine_manifest.txt"
    if manifest_txt.exists():
        with open(manifest_txt, "r", encoding="utf-8") as f:
            lineas = f.readlines()
            archivos_validados = int(lineas[0].split(":")[1].strip())
            archivos_rechazados = int(lineas[1].split(":")[1].strip())

    metricas = {
        "calidad_iso_25012": {
            "tasa_completitud_porcentaje": round(float(tasa_completitud), 2),
            "integridad_criptografica": {
                "archivos_validados": archivos_validados,
                "archivos_rechazados": archivos_rechazados
            }
        },
        "distribucion_importe_eur": {
            "media": round(float(df_validos["importe_eur"].mean()), 2),
            "mediana": round(float(df_validos["importe_eur"].median()), 2),
            "desviacion_estandar": round(float(df_validos["importe_eur"].std()), 2),
            "percentil_25": round(float(df_validos["importe_eur"].quantile(0.25)), 2),
            "percentil_75": round(float(df_validos["importe_eur"].quantile(0.75)), 2)
        }
    }

    ruta_metricas = output_dir / "metricas_perfilado.json"
    with open(ruta_metricas, "w", encoding="utf-8") as json_file:
        json.dump(metricas, json_file, indent=4, ensure_ascii=False)

    logging.info("Métricas de perfilado exportadas a JSON.")
    print(f"[OK] Dataset limpio guardado en: processed/dataset_kdd_listo.csv ({len(df_validos)} filas)")
    print(f"[OK] Métricas guardadas en: output_samples/metricas_perfilado.json")

if __name__ == "__main__":
    logging.info("Iniciando pipeline de saneamiento (Fase 2 y 3)...")
    ejecutar_pipeline_saneamiento()