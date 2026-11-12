"""
02_pipeline_saneamiento.py
Fase 2 - Limpieza, coherencia y detección de outliers sobre staging/verified/
(Fase 3 se añadirá en los siguientes pasos)

Uso (desde la raíz del proyecto, DESPUÉS de 01_verificar_integridad.py):
    python scripts/02_pipeline_saneamiento.py
"""

import logging
from pathlib import Path

import pandas as pd

# --- Rutas ---
BASE_DIR = Path(__file__).resolve().parent.parent
VERIFIED_DIR = BASE_DIR / "staging" / "verified"
QUARANTINE_DIR = BASE_DIR / "quarantine"
BAD_RECORDS = QUARANTINE_DIR / "bad_records.csv"
LOG_FILE = BASE_DIR / "logs" / "ejecucion_pipeline.log"

# --- Reglas de negocio ---
COLUMNAS_OBLIGATORIAS = ["id_transaccion", "timestamp", "importe_eur", "unidades"]
COLUMNAS_SECUNDARIAS = ["tienda", "categoria", "metodo_pago"]
VALOR_IMPUTACION_CATEGORICA = "Desconocido"


def configurar_log():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [FASE2] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


# ---------------------------------------------------------------------------
# PASO 3: Carga, concatenación y tratamiento de nulos
# ---------------------------------------------------------------------------
def cargar_verificados():
    """Carga y concatena todos los CSV que superaron la Fase 1.
    Se lee todo como texto (dtype=str) para que pandas no 'arregle' nada
    por su cuenta: los tipos se convierten y validan después, de forma controlada."""
    ficheros = sorted(VERIFIED_DIR.glob("*.csv"))
    if not ficheros:
        raise FileNotFoundError("No hay ficheros en staging/verified/. Ejecuta antes la Fase 1.")

    partes = []
    for fichero in ficheros:
        df = pd.read_csv(fichero, dtype=str)
        df["origen_fichero"] = fichero.name  # trazabilidad: de qué fichero viene cada fila
        logging.info("Cargado %s: %d registros", fichero.name, len(df))
        partes.append(df)

    df = pd.concat(partes, ignore_index=True)
    # Cadenas vacías o solo espacios -> nulo real
    df = df.replace(r"^\s*$", pd.NA, regex=True)
    logging.info("Total registros cargados: %d", len(df))
    return df


def tratar_nulos(df, rechazados):
    """- Nulo en columna obligatoria -> el registro va a cuarentena (no se inventa).
    - Nulo en columna secundaria categórica -> se imputa 'Desconocido'."""
    nulos_por_columna = df.isna().sum()
    for col, n in nulos_por_columna[nulos_por_columna > 0].items():
        logging.info("Nulos detectados en '%s': %d", col, n)

    # 1) Obligatorias: descartar a cuarentena indicando el motivo
    for col in COLUMNAS_OBLIGATORIAS:
        mascara = df[col].isna()
        if mascara.any():
            malos = df[mascara].copy()
            malos["motivo_rechazo"] = f"NULO_EN_{col.upper()}"
            rechazados.append(malos)
            logging.warning("Rechazados %d registros por nulo en '%s'", mascara.sum(), col)
            df = df[~mascara]

    # 2) Secundarias: imputar
    for col in COLUMNAS_SECUNDARIAS:
        n = df[col].isna().sum()
        if n:
            df[col] = df[col].fillna(VALOR_IMPUTACION_CATEGORICA)
            logging.info("Imputados %d nulos en '%s' con '%s'", n, col, VALOR_IMPUTACION_CATEGORICA)

    return df


# ---------------------------------------------------------------------------
# PASO 4: Coherencia temporal
# ---------------------------------------------------------------------------
def validar_timestamps(df, rechazados):
    """- Convierte 'timestamp' a fecha real. Lo que no se pueda interpretar -> NaT.
    - Rechaza: fechas inválidas, fechas futuras y fechas anteriores al año en curso.
    - Deja la columna en formato ISO 8601: YYYY-MM-DD HH:MM:SS."""
    ahora = pd.Timestamp.now()
    inicio_anio = pd.Timestamp(year=ahora.year, month=1, day=1)

    fechas = pd.to_datetime(df["timestamp"], format="%Y-%m-%d %H:%M:%S", errors="coerce")

    reglas = {
        "TIMESTAMP_INVALIDO": fechas.isna(),
        "TIMESTAMP_FUTURO": fechas > ahora,
        "TIMESTAMP_ANTERIOR_AL_ANIO_EN_CURSO": fechas < inicio_anio,
    }

    for motivo, mascara in reglas.items():
        if mascara.any():
            malos = df[mascara].copy()
            malos["motivo_rechazo"] = motivo
            rechazados.append(malos)
            for _, fila in malos.iterrows():
                logging.warning("%s: %s (timestamp=%r)", motivo, fila["id_transaccion"], fila["timestamp"])

    validos = ~(reglas["TIMESTAMP_INVALIDO"] | reglas["TIMESTAMP_FUTURO"]
                | reglas["TIMESTAMP_ANTERIOR_AL_ANIO_EN_CURSO"])
    df = df[validos].copy()
    df["timestamp"] = fechas[validos].dt.strftime("%Y-%m-%d %H:%M:%S")
    logging.info("Validación temporal: %d registros rechazados", (~validos).sum())
    return df


# ---------------------------------------------------------------------------
# PASO 5: Reglas de dominio
# ---------------------------------------------------------------------------
def validar_dominio(df, rechazados):
    """- Convierte importe_eur a decimal y unidades a número.
    - Rechaza: valores no numéricos, importe_eur <= 0, unidades < 1 o no enteras."""
    importe = pd.to_numeric(df["importe_eur"], errors="coerce")
    unidades = pd.to_numeric(df["unidades"], errors="coerce")

    # Se evalúan en orden: cada registro se rechaza por el PRIMER motivo que incumple
    reglas = [
        ("IMPORTE_NO_NUMERICO", importe.isna()),
        ("UNIDADES_NO_NUMERICAS", unidades.isna()),
        ("IMPORTE_NO_POSITIVO", importe <= 0),
        ("UNIDADES_MENOR_QUE_1", unidades < 1),
        ("UNIDADES_NO_ENTERAS", unidades % 1 != 0),
    ]

    ya_rechazado = pd.Series(False, index=df.index)
    for motivo, mascara in reglas:
        mascara = mascara & ~ya_rechazado
        if mascara.any():
            malos = df[mascara].copy()
            malos["motivo_rechazo"] = motivo
            rechazados.append(malos)
            for _, fila in malos.iterrows():
                logging.warning("%s: %s (importe_eur=%s, unidades=%s)",
                                motivo, fila["id_transaccion"], fila["importe_eur"], fila["unidades"])
        ya_rechazado |= mascara

    df = df[~ya_rechazado].copy()
    # A partir de aquí las columnas ya tienen su tipo correcto
    df["importe_eur"] = importe[~ya_rechazado].astype(float)
    df["unidades"] = unidades[~ya_rechazado].astype(int)
    logging.info("Validación de dominio: %d registros rechazados", ya_rechazado.sum())
    return df


# ---------------------------------------------------------------------------
# PASO 6: Detección de outliers (método IQR / Tukey)
# ---------------------------------------------------------------------------
FACTOR_IQR = 1.5


def detectar_outliers(df, rechazados, columna="importe_eur"):
    """Un valor es outlier si cae fuera de [Q1 - 1.5*IQR, Q3 + 1.5*IQR],
    siendo IQR = Q3 - Q1. Se usa IQR (y no media ± 3·desviación) porque los
    propios outliers inflan la media y la desviación, y el IQR no se deja arrastrar."""
    q1 = df[columna].quantile(0.25)
    q3 = df[columna].quantile(0.75)
    iqr = q3 - q1
    limite_inf = q1 - FACTOR_IQR * iqr
    limite_sup = q3 + FACTOR_IQR * iqr
    logging.info("Outliers '%s': Q1=%.2f Q3=%.2f IQR=%.2f -> rango válido [%.2f, %.2f]",
                 columna, q1, q3, iqr, limite_inf, limite_sup)

    mascara = (df[columna] < limite_inf) | (df[columna] > limite_sup)
    if mascara.any():
        malos = df[mascara].copy()
        malos["motivo_rechazo"] = f"OUTLIER_IQR_{columna.upper()}"
        rechazados.append(malos)
        for _, fila in malos.iterrows():
            logging.warning("OUTLIER: %s (%s=%.2f fuera de [%.2f, %.2f])",
                            fila["id_transaccion"], columna, fila[columna], limite_inf, limite_sup)

    logging.info("Detección de outliers: %d registros rechazados", mascara.sum())
    return df[~mascara].copy()


# ---------------------------------------------------------------------------
# PASO 7 (FASE 3): Unicidad y exportación conforme
# ---------------------------------------------------------------------------
PROCESSED_DIR = BASE_DIR / "processed"
DATASET_FINAL = PROCESSED_DIR / "dataset_kdd_listo.csv"
ORDEN_COLUMNAS = ["id_transaccion", "tienda", "timestamp", "categoria",
                  "importe_eur", "unidades", "metodo_pago", "origen_fichero"]


def validar_unicidad(df, rechazados):
    """id_transaccion es la clave: no puede repetirse. Se conserva la primera
    aparición y las repetidas van a cuarentena."""
    mascara = df.duplicated(subset="id_transaccion", keep="first")
    if mascara.any():
        malos = df[mascara].copy()
        malos["motivo_rechazo"] = "ID_DUPLICADO"
        rechazados.append(malos)
        for id_dup in malos["id_transaccion"]:
            logging.warning("ID_DUPLICADO: %s", id_dup)
    logging.info("Validación de unicidad: %d duplicados", mascara.sum())
    return df[~mascara].copy()


def exportar_dataset(df):
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df = df[ORDEN_COLUMNAS].sort_values("timestamp").reset_index(drop=True)
    df.to_csv(DATASET_FINAL, index=False, encoding="utf-8")
    logging.info("Dataset limpio exportado: %d registros -> processed/%s",
                 len(df), DATASET_FINAL.name)
    return df


# ---------------------------------------------------------------------------
# PASO 8 (FASE 3): Reporte de perfilado (ISO/IEC 25012)
# ---------------------------------------------------------------------------
METRICAS_JSON = BASE_DIR / "output_samples" / "metricas_perfilado.json"
TAMPERED_DIR = BASE_DIR / "quarantine" / "tampered"


def generar_perfilado(df_final, malos, total_inicial, registros_sin_nulos):
    import json

    # Integridad criptográfica: se lee lo que dejó la Fase 1 en disco
    validados = len(list(VERIFIED_DIR.glob("*.csv")))
    rechazados_hash = len(list(TAMPERED_DIR.glob("*.csv")))
    total_ficheros = validados + rechazados_hash

    imp = df_final["importe_eur"]
    metricas = {
        "lote": "raw_batch_202611",
        "fecha_ejecucion": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "integridad_criptografica": {
            "ficheros_totales": total_ficheros,
            "ficheros_validados": validados,
            "ficheros_rechazados": rechazados_hash,
            "tasa_integridad_pct": round(100 * validados / total_ficheros, 2),
        },
        "completitud": {
            "registros_totales": total_inicial,
            "registros_sin_nulos": registros_sin_nulos,
            "tasa_completitud_bruto_pct": round(100 * registros_sin_nulos / total_inicial, 2),
            "tasa_completitud_final_pct": round(100 * df_final.notna().all(axis=1).mean(), 2),
        },
        "unicidad": {
            "ids_unicos_final": int(df_final["id_transaccion"].nunique()),
            "tasa_unicidad_final_pct": round(
                100 * df_final["id_transaccion"].nunique() / len(df_final), 2),
        },
        "validez": {
            "registros_validos": len(df_final),
            "registros_en_cuarentena": len(malos),
            "tasa_validez_pct": round(100 * len(df_final) / total_inicial, 2),
            "rechazos_por_motivo": {k: int(v) for k, v in
                                    malos["motivo_rechazo"].value_counts().items()},
        },
        "distribucion_importe_eur": {
            "media": round(float(imp.mean()), 2),
            "mediana": round(float(imp.median()), 2),
            "desviacion_estandar": round(float(imp.std()), 2),
            "p25": round(float(imp.quantile(0.25)), 2),
            "p75": round(float(imp.quantile(0.75)), 2),
            "minimo": round(float(imp.min()), 2),
            "maximo": round(float(imp.max()), 2),
        },
    }

    METRICAS_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(METRICAS_JSON, "w", encoding="utf-8") as f:
        json.dump(metricas, f, indent=2, ensure_ascii=False)

    logging.info("Perfilado: integridad=%.2f%% completitud_bruto=%.2f%% validez=%.2f%% unicidad=%.2f%%",
                 metricas["integridad_criptografica"]["tasa_integridad_pct"],
                 metricas["completitud"]["tasa_completitud_bruto_pct"],
                 metricas["validez"]["tasa_validez_pct"],
                 metricas["unicidad"]["tasa_unicidad_final_pct"])
    logging.info("Perfilado importe_eur: media=%.2f mediana=%.2f std=%.2f p25=%.2f p75=%.2f",
                 *[metricas["distribucion_importe_eur"][k]
                   for k in ("media", "mediana", "desviacion_estandar", "p25", "p75")])
    logging.info("Métricas guardadas en output_samples/%s", METRICAS_JSON.name)
    return metricas


def guardar_cuarentena(rechazados):
    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
    if rechazados:
        malos = pd.concat(rechazados, ignore_index=True)
    else:
        malos = pd.DataFrame(columns=["motivo_rechazo"])
    malos.to_csv(BAD_RECORDS, index=False)
    logging.info("Registros en cuarentena: %d -> quarantine/bad_records.csv", len(malos))
    return malos


def main():
    configurar_log()
    logging.info("=== Inicio pipeline de saneamiento ===")
    rechazados = []  # aquí se van acumulando los registros no conformes

    df = cargar_verificados()
    total_inicial = len(df)
    registros_sin_nulos = int(df.notna().all(axis=1).sum())  # para la completitud (Fase 3)
    logging.info("Completitud del lote en bruto: %d/%d registros sin nulos (%.2f %%)",
                 registros_sin_nulos, total_inicial, 100 * registros_sin_nulos / total_inicial)

    df = tratar_nulos(df, rechazados)
    df = validar_timestamps(df, rechazados)
    df = validar_dominio(df, rechazados)
    df = detectar_outliers(df, rechazados, "importe_eur")
    df = validar_unicidad(df, rechazados)
    df = exportar_dataset(df)

    malos = guardar_cuarentena(rechazados)
    generar_perfilado(df, malos, total_inicial, registros_sin_nulos)
    logging.info("Registros que continúan en el pipeline: %d", len(df))
    logging.info("=== Fin pipeline de saneamiento ===")


if __name__ == "__main__":
    main()