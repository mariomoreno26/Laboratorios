"""
01_verificar_integridad.py
Fase 1 - Pasarela de integridad criptográfica (SHA-256) por lotes.

- Lee línea a línea raw_batch_202611/manifest_checksums.sha256
- Calcula el SHA-256 de cada fichero del lote
- Si coincide  -> copia a staging/verified/
- Si no coincide -> copia a quarantine/tampered/ y emite alerta en el log
- Genera output_samples/quarantine_manifest.txt con los ficheros rechazados

Uso (desde la raíz del proyecto):
    python3 scripts/01_verificar_integridad.py
"""

import hashlib
import logging
import shutil
from pathlib import Path

# --- Rutas (relativas a la raíz del proyecto, no a donde se ejecute) ---
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "raw_batch_202611"
MANIFEST = RAW_DIR / "manifest_checksums.sha256"
VERIFIED_DIR = BASE_DIR / "staging" / "verified"
TAMPERED_DIR = BASE_DIR / "quarantine" / "tampered"
LOG_FILE = BASE_DIR / "logs" / "ejecucion_pipeline.log"
QUARANTINE_MANIFEST = BASE_DIR / "output_samples" / "quarantine_manifest.txt"


def configurar_log():
    """Log a fichero (append) y a terminal a la vez."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [FASE1] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def calcular_sha256(ruta_fichero):
    """Calcula el SHA-256 leyendo por bloques de 64 KB (sirve para ficheros grandes)."""
    hasher = hashlib.sha256()
    with open(ruta_fichero, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def leer_manifiesto(ruta_manifiesto):
    """Devuelve un diccionario {nombre_fichero: hash_esperado}.
    Formato de cada línea: '<hash>  <nombre_fichero>' (formato sha256sum)."""
    esperados = {}
    with open(ruta_manifiesto, "r", encoding="utf-8") as f:
        for num_linea, linea in enumerate(f, start=1):
            linea = linea.strip()
            if not linea:
                continue  # saltar líneas vacías
            partes = linea.split(maxsplit=1)
            if len(partes) != 2:
                logging.warning("Línea %d del manifiesto mal formada: %r", num_linea, linea)
                continue
            hash_esperado, nombre = partes
            nombre = nombre.lstrip("*")  # sha256sum en modo binario añade '*'
            esperados[nombre] = hash_esperado.lower()
    return esperados


def main():
    configurar_log()
    logging.info("=== Inicio verificación de integridad del lote %s ===", RAW_DIR.name)

    VERIFIED_DIR.mkdir(parents=True, exist_ok=True)
    TAMPERED_DIR.mkdir(parents=True, exist_ok=True)

    esperados = leer_manifiesto(MANIFEST)
    logging.info("Manifiesto cargado: %d firmas oficiales", len(esperados))

    validados, rechazados = [], []

    for nombre, hash_esperado in esperados.items():
        ruta = RAW_DIR / nombre

        if not ruta.exists():
            logging.error("FALTA FICHERO: %s aparece en el manifiesto pero no en el lote", nombre)
            rechazados.append((nombre, hash_esperado, "NO_ENCONTRADO"))
            continue

        hash_calculado = calcular_sha256(ruta)

        if hash_calculado == hash_esperado:
            shutil.copy2(ruta, VERIFIED_DIR / nombre)
            logging.info("OK      %s -> staging/verified/", nombre)
            validados.append(nombre)
        else:
            shutil.copy2(ruta, TAMPERED_DIR / nombre)
            logging.warning(
                "ALERTA  %s FIRMA DISCREPANTE -> quarantine/tampered/ "
                "(esperado=%s... calculado=%s...)",
                nombre, hash_esperado[:16], hash_calculado[:16],
            )
            rechazados.append((nombre, hash_esperado, hash_calculado))

    # Ficheros que están en el lote pero no figuran en el manifiesto
    for ruta in RAW_DIR.glob("*.csv"):
        if ruta.name not in esperados:
            shutil.copy2(ruta, TAMPERED_DIR / ruta.name)
            logging.warning("ALERTA  %s no figura en el manifiesto -> quarantine/tampered/", ruta.name)
            rechazados.append((ruta.name, "SIN_FIRMA", calcular_sha256(ruta)))

    # Manifiesto de cuarentena (evidencia para output_samples/)
    QUARANTINE_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with open(QUARANTINE_MANIFEST, "w", encoding="utf-8") as f:
        f.write("# fichero | hash_esperado | hash_calculado\n")
        for nombre, esp, calc in rechazados:
            f.write(f"{nombre} | {esp} | {calc}\n")

    total = len(validados) + len(rechazados)
    logging.info(
        "Resumen Fase 1: %d validados, %d rechazados de %d (integridad %.2f %%)",
        len(validados), len(rechazados), total,
        100 * len(validados) / total if total else 0,
    )
    logging.info("=== Fin verificación de integridad ===")


if __name__ == "__main__":
    main()