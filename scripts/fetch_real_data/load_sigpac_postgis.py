"""
load_sigpac_postgis.py
======================
Carga los ficheros GML o GeoPackage descargados del FEGA a PostGIS.

Usa ogr2ogr (GDAL) para la conversión y carga, que maneja todos los formatos
SIGPAC (GML 3.2, GeoPackage, Shapefile) de forma robusta y eficiente.

Uso:
    # Carga todo lo descargado por fetch_sigpac_atom.py
    python load_sigpac_postgis.py --input-dir data/sigpac_raw

    # Solo una provincia
    python load_sigpac_postgis.py --input-dir data/sigpac_raw --provincias 36

    # Previsualizar sin cargar (dry-run)
    python load_sigpac_postgis.py --input-dir data/sigpac_raw --dry-run

Requisitos:
    - GDAL/ogr2ogr instalado (viene con PostGIS Docker o: apt install gdal-bin)
    - psycopg2: pip install psycopg2-binary
    - Variables de entorno: POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB,
      POSTGRES_USER, POSTGRES_PASSWORD (o editar DB_CONFIG abajo)
"""

from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
LOGGER = logging.getLogger("load_sigpac_postgis")

# ---------------------------------------------------------------------------
# Configuración de base de datos
# Usa variables de entorno (igual que el resto del proyecto TerraGalicia)
# ---------------------------------------------------------------------------

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "dbname": os.getenv("POSTGRES_DB", "terragalicia"),
    "user": os.getenv("POSTGRES_USER", "terragalicia"),
    "password": os.getenv("POSTGRES_PASSWORD", "terragalicia"),
}

# Tabla destino en PostGIS
TARGET_TABLE = "recintos_sigpac"
TARGET_SCHEMA = "public"

# SRID de origen en los ficheros SIGPAC del FEGA (ETRS89 / UTM zone 29N para Galicia)
# El FEGA publica en EPSG:25829 (Galicia) o EPSG:4258 (ETRS89 geográfico)
# ogr2ogr reproyecta automáticamente a WGS84 (4326) para PostGIS
SOURCE_SRID = "EPSG:25829"
TARGET_SRID = "EPSG:4326"

# Extensiones que buscamos dentro de los ZIPs extraídos
GEO_EXTENSIONS = {".gml", ".gpkg", ".shp"}

# Capa dentro del GeoPackage/GML que contiene los recintos
# En los ficheros del FEGA suele llamarse "RECINTO" o "recintos"
LAYER_NAMES = ["RECINTO", "recintos", "Recinto"]

# ---------------------------------------------------------------------------
# SQL de inicialización de la tabla
# ---------------------------------------------------------------------------

CREATE_TABLE_SQL = f"""
-- Tabla principal de recintos SIGPAC para TerraGalicia DSS
CREATE TABLE IF NOT EXISTS {TARGET_SCHEMA}.{TARGET_TABLE} (
    ogc_fid         SERIAL PRIMARY KEY,
    -- Identificadores SIGPAC
    provincia       SMALLINT,
    municipio       SMALLINT,
    agregado        SMALLINT,
    zona            SMALLINT,
    poligono        INTEGER,
    parcela         INTEGER,
    recinto         SMALLINT,
    -- Atributos agronómicos
    uso_sigpac      VARCHAR(4),          -- Código de uso del suelo
    coef_regadio    NUMERIC(5,2),        -- Coeficiente de regadío 0-100
    superficie      NUMERIC(12,4),       -- Superficie en m²
    perimetro       NUMERIC(12,4),       -- Perímetro en metros
    altitud         NUMERIC(8,2),        -- Altitud media (desde campaña 2024)
    pendiente_media NUMERIC(6,2),
    -- Incidencias SIGPAC (campo de texto libre con códigos separados por comas)
    incidencias     TEXT,
    -- Geometría en WGS84
    geom            GEOMETRY(MULTIPOLYGON, 4326),
    -- Metadatos de carga
    campana         SMALLINT,            -- Año de campaña
    fecha_carga     TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índice espacial (imprescindible para consultas bbox)
CREATE INDEX IF NOT EXISTS {TARGET_TABLE}_geom_idx
    ON {TARGET_SCHEMA}.{TARGET_TABLE} USING GIST (geom);

-- Índice por provincia+municipio (para queries por zona)
CREATE INDEX IF NOT EXISTS {TARGET_TABLE}_prov_mun_idx
    ON {TARGET_SCHEMA}.{TARGET_TABLE} (provincia, municipio);

-- Índice por uso del suelo
CREATE INDEX IF NOT EXISTS {TARGET_TABLE}_uso_idx
    ON {TARGET_SCHEMA}.{TARGET_TABLE} (uso_sigpac);
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def pg_connection_string() -> str:
    """Construye el connection string para ogr2ogr."""
    c = DB_CONFIG
    return (
        f"PG:host={c['host']} port={c['port']} dbname={c['dbname']} "
        f"user={c['user']} password={c['password']}"
    )


def init_table(dry_run: bool = False) -> None:
    """Crea la tabla en PostGIS si no existe."""
    if dry_run:
        LOGGER.info("[dry-run] Se ejecutaría el SQL de creación de tabla")
        return
    try:
        import psycopg2  # noqa: PLC0415

        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
        conn.close()
        LOGGER.info("Tabla %s.%s lista en PostGIS", TARGET_SCHEMA, TARGET_TABLE)
    except ImportError:
        LOGGER.warning("psycopg2 no instalado — asumiendo que la tabla ya existe")
    except Exception as exc:  # noqa: BLE001
        LOGGER.error("Error inicializando tabla: %s", exc)
        raise


def find_geo_files(input_dir: Path) -> list[Path]:
    """Busca recursivamente todos los ficheros geográficos."""
    found: list[Path] = []
    for ext in GEO_EXTENSIONS:
        found.extend(input_dir.rglob(f"*{ext}"))
    # Preferir GML sobre SHP si ambos existen para el mismo municipio
    found.sort()
    return found


def detect_layer(filepath: Path) -> str | None:
    """Detecta el nombre de capa correcto dentro del fichero."""
    result = subprocess.run(
        ["ogrinfo", "-al", "-so", str(filepath)],
        capture_output=True,
        text=True,
    )
    for layer_name in LAYER_NAMES:
        if layer_name.upper() in result.stdout.upper():
            return layer_name
    # Si no encontramos ninguno conocido, devolver None (ogr2ogr usará la primera)
    return None


def load_file(filepath: Path, dry_run: bool = False, append: bool = True) -> bool:
    """
    Carga un fichero GML/GeoPackage/SHP a PostGIS via ogr2ogr.

    Parámetros ogr2ogr relevantes:
      -append        — añadir a la tabla existente (no recrear)
      -update        — actualizar la BD existente
      -nln           — nombre de la tabla destino
      -t_srs         — reproyectar al SRS objetivo
      -s_srs         — SRS de origen (por si el fichero no lo declara)
      -dim XY        — forzar 2D (los GML del FEGA a veces vienen con Z=0)
      -nlt PROMOTE_TO_MULTI — convertir Polygon a MultiPolygon para consistencia
    """
    layer = detect_layer(filepath)

    cmd = [
        "ogr2ogr",
        "-f", "PostgreSQL",
        pg_connection_string(),
        str(filepath),
        "-nln", f"{TARGET_SCHEMA}.{TARGET_TABLE}",
        "-t_srs", TARGET_SRID,
        "-s_srs", SOURCE_SRID,
        "-dim", "XY",
        "-nlt", "PROMOTE_TO_MULTI",
        "--config", "OGR_TRUNCATE", "NO",
        "-progress",
    ]

    if append:
        cmd.extend(["-append", "-update"])

    if layer:
        cmd.append(layer)

    LOGGER.info("Cargando: %s (capa: %s)", filepath.name, layer or "auto")
    LOGGER.debug("Comando: %s", " ".join(cmd))

    if dry_run:
        LOGGER.info("[dry-run] %s", " ".join(cmd))
        return True

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            LOGGER.error("ogr2ogr falló para %s:\n%s", filepath.name, result.stderr)
            return False
        LOGGER.info("  OK: %s", filepath.name)
        return True
    except subprocess.TimeoutExpired:
        LOGGER.error("Timeout cargando %s", filepath.name)
        return False
    except FileNotFoundError:
        LOGGER.error(
            "ogr2ogr no encontrado. Instala GDAL:\n"
            "  Ubuntu/Debian: sudo apt install gdal-bin\n"
            "  macOS:         brew install gdal\n"
            "  Docker:        ya disponible en la imagen PostGIS"
        )
        sys.exit(1)


def run_post_load_sql(dry_run: bool = False) -> None:
    """
    Ejecuta SQL de limpieza/optimización tras la carga.
    - Elimina duplicados por referencia SIGPAC completa
    - Actualiza VACUUM ANALYZE
    """
    sql = f"""
    -- Eliminar duplicados (conservar el más reciente)
    DELETE FROM {TARGET_SCHEMA}.{TARGET_TABLE} a
    USING {TARGET_SCHEMA}.{TARGET_TABLE} b
    WHERE a.ogc_fid < b.ogc_fid
      AND a.provincia = b.provincia
      AND a.municipio = b.municipio
      AND a.poligono  = b.poligono
      AND a.parcela   = b.parcela
      AND a.recinto   = b.recinto;

    -- Actualizar estadísticas del planificador
    ANALYZE {TARGET_SCHEMA}.{TARGET_TABLE};
    """
    if dry_run:
        LOGGER.info("[dry-run] Post-load SQL omitido")
        return
    try:
        import psycopg2  # noqa: PLC0415

        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.close()
        LOGGER.info("Post-load SQL completado (deduplicación + ANALYZE)")
    except ImportError:
        LOGGER.warning("psycopg2 no disponible — ejecuta manualmente el SQL de deduplicación")
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("Post-load SQL falló (no crítico): %s", exc)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Carga ficheros GML/GeoPackage SIGPAC a PostGIS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--input-dir",
        default="data/sigpac_raw",
        help="Directorio con los ficheros descargados por fetch_sigpac_atom.py",
    )
    parser.add_argument(
        "--provincias",
        nargs="+",
        default=None,
        metavar="COD",
        help="Filtrar por código de provincia (p.ej. 36)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostrar qué se haría sin ejecutar nada",
    )
    parser.add_argument(
        "--no-dedup",
        action="store_true",
        help="Saltar la deduplicación post-carga",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        LOGGER.error("Directorio no encontrado: %s", input_dir)
        LOGGER.error("Ejecuta primero: python fetch_sigpac_atom.py --output-dir %s", input_dir)
        return 1

    # Filtrar por provincia si se especifica
    if args.provincias:
        search_dirs = [input_dir / f"prov_{p.zfill(2)}" for p in args.provincias]
    else:
        search_dirs = [input_dir]

    # Recopilar ficheros
    all_files: list[Path] = []
    for d in search_dirs:
        all_files.extend(find_geo_files(d))

    if not all_files:
        LOGGER.error("No se encontraron ficheros GML/GPKG/SHP en %s", input_dir)
        return 1

    LOGGER.info("Ficheros a cargar: %d", len(all_files))

    # Inicializar tabla
    init_table(dry_run=args.dry_run)

    # Cargar ficheros
    ok = 0
    failed = 0
    # El primer fichero hace -overwrite implícito si la tabla está vacía,
    # los siguientes hacen -append.
    for i, fpath in enumerate(all_files):
        success = load_file(fpath, dry_run=args.dry_run, append=True)
        if success:
            ok += 1
        else:
            failed += 1

    LOGGER.info("=== Carga completada: %d OK, %d errores ===", ok, failed)

    if not args.no_dedup and not args.dry_run:
        run_post_load_sql(dry_run=args.dry_run)

    LOGGER.info(
        "Siguiente paso: levanta el backend FastAPI y llama a GET /api/v1/sigpac/parcels?bbox=..."
    )
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())