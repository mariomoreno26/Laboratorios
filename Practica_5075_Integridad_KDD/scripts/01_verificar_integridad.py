import hashlib
import shutil
import logging
from pathlib import Path

# Ruta raíz del proyecto (Practica_5075_Integridad_KDD/) independiente de desde dónde se ejecute
BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "ejecucion_pipeline.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

def calcular_sha256(ruta_fichero: Path) -> str:
    """Calcula el hash SHA-256 de un fichero leyendo en bloques de 64KB."""
    hasher = hashlib.sha256()
    with open(ruta_fichero, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def validar_lote():
    raw_dir = BASE_DIR / "raw_batch_202611"
    manifest_path = raw_dir / "manifest_checksums.sha256"

    staging_dir = BASE_DIR / "staging" / "verified"
    quarantine_dir = BASE_DIR / "quarantine" / "tampered"
    output_dir = BASE_DIR / "output_samples"

    staging_dir.mkdir(parents=True, exist_ok=True)
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not manifest_path.exists():
        msg = f"No se encuentra el manifiesto en: {manifest_path}"
        logging.error(msg)
        print(f"[ERROR] {msg}")
        return

    # Leer manifiesto ignorando posible BOM de Windows (utf-8-sig)
    firmas_esperadas = {}
    with open(manifest_path, "r", encoding="utf-8-sig") as m:
        for linea in m:
            partes = linea.strip().split()
            if len(partes) >= 2:
                nombre = Path(partes[1].lstrip("*")).name
                firmas_esperadas[nombre] = partes[0].lower()

    archivos_procesados = 0
    archivos_rechazados = 0

    for archivo in sorted(raw_dir.glob("*.csv")):
        nombre_fichero = archivo.name
        if nombre_fichero in firmas_esperadas:
            hash_calculado = calcular_sha256(archivo).lower()
            hash_esperado = firmas_esperadas[nombre_fichero]

            if hash_calculado == hash_esperado:
                shutil.copy2(archivo, staging_dir / nombre_fichero)
                logging.info(f"INTEGRIDAD OK: {nombre_fichero} movido a staging/verified/")
                print(f"[OK] {nombre_fichero} -> staging/verified/")
                archivos_procesados += 1
            else:
                shutil.copy2(archivo, quarantine_dir / nombre_fichero)
                logging.warning(f"CORRUPCIÓN DETECTADA: {nombre_fichero} movido a quarantine/tampered/")
                print(f"[ALERTA] {nombre_fichero} -> quarantine/tampered/ (hash no coincide)")
                archivos_rechazados += 1

    with open(output_dir / "quarantine_manifest.txt", "w", encoding="utf-8") as f:
        f.write(f"Archivos Validados: {archivos_procesados}\n")
        f.write(f"Archivos Rechazados: {archivos_rechazados}\n")

    print(f"Resumen Fase 1 -> Validados: {archivos_procesados} | Rechazados: {archivos_rechazados}")

if __name__ == "__main__":
    logging.info("Iniciando validación criptográfica (Fase 1)...")
    validar_lote()
    logging.info("Validación finalizada.")