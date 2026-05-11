# SCRIPTS DE IMPLEMENTACIÓN — Arquitectura SIGPAC Recomendada
## TerraGalicia DSS — Ingesta Offline + PostGIS Local

---

## Script 1: Descarga Inicial ATOM + Carga PostGIS

**Archivo:** `scripts/setup_sigpac_initial.sh`

Ejecutar UNA sola vez para setup inicial.

```bash
#!/bin/bash
#
# setup_sigpac_initial.sh
# =====================
# Descarga y carga inicial de SIGPAC desde FEGA ATOM a PostGIS
#
# Uso:
#   bash scripts/setup_sigpac_initial.sh
#   bash scripts/setup_sigpac_initial.sh --dry-run    # Ver qué se haría
#   bash scripts/setup_sigpac_initial.sh --provincias 15 36  # Solo A Coruña + Pontevedra
#

set -e

# Configuración
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOWNLOAD_DIR="${PROJECT_ROOT}/data/sigpac_raw"
BACKUP_DIR="${PROJECT_ROOT}/backups"
LOG_FILE="${PROJECT_ROOT}/logs/sigpac_setup_$(date +%Y%m%d_%H%M%S).log"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Defaults
DRY_RUN=false
PROVINCIAS=("15" "27" "32" "36")  # Todas las provincias gallegas
CONCURRENT=2

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --provincias)
            shift
            PROVINCIAS=()
            while [[ $# -gt 0 && $1 != --* ]]; do
                PROVINCIAS+=("$1")
                shift
            done
            ;;
        --concurrent)
            CONCURRENT=$2
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Logging
mkdir -p "$(dirname "$LOG_FILE")" "$BACKUP_DIR"

log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

log_info() {
    log "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    log "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    log "${RED}[ERROR]${NC} $1"
}

# ============================================================================
# VALIDACIÓN DE REQUISITOS
# ============================================================================

log_info "Validando requisitos..."

# Check Python
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 no encontrado"
    exit 1
fi
log_info "✅ Python 3 encontrado: $(python3 --version)"

# Check ogr2ogr (GDAL)
if ! command -v ogr2ogr &> /dev/null; then
    log_error "ogr2ogr (GDAL) no encontrado"
    log_error "Instala con:"
    log_error "  Ubuntu: sudo apt install gdal-bin"
    log_error "  macOS: brew install gdal"
    exit 1
fi
log_info "✅ ogr2ogr encontrado: $(ogr2ogr --version | head -1)"

# Check psycopg2 (Python PostgreSQL driver)
if ! python3 -c "import psycopg2" 2>/dev/null; then
    log_warn "psycopg2 no instalado. Se usará solo ogr2ogr para la carga."
    log_warn "Para mejor control, ejecuta: pip install psycopg2-binary"
fi

# Check PostgreSQL connectivity
if command -v psql &> /dev/null; then
    PG_HOST="${POSTGRES_HOST:-localhost}"
    PG_PORT="${POSTGRES_PORT:-5432}"
    PG_DB="${POSTGRES_DB:-terragalicia}"
    PG_USER="${POSTGRES_USER:-terragalicia}"
    
    if psql -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$PG_DB" \
        -c "SELECT 1" &>/dev/null; then
        log_info "✅ PostgreSQL conectado: ${PG_HOST}:${PG_PORT}/${PG_DB}"
    else
        log_error "No se pudo conectar a PostgreSQL"
        log_error "Asegúrate de que docker-compose está ejecutándose:"
        log_error "  cd infra && docker-compose up -d"
        exit 1
    fi
else
    log_warn "psql no encontrado. Se asume que PostgreSQL es accesible vía env vars"
fi

# ============================================================================
# DESCARGA DE ATOM
# ============================================================================

log_info "Iniciando descarga de SIGPAC ATOM..."
log_info "Provincias: ${PROVINCIAS[@]}"
log_info "Concurrencia: $CONCURRENT"
log_info "Destino: $DOWNLOAD_DIR"

if [ "$DRY_RUN" = true ]; then
    log_warn "[DRY-RUN] Los siguientes comandos se ejecutarían:"
    log_warn "  python3 scripts/fetch_real_data/fetch_sigpac_atom.py \\"
    log_warn "    --output-dir $DOWNLOAD_DIR \\"
    log_warn "    --provincias ${PROVINCIAS[@]} \\"
    log_warn "    --concurrent $CONCURRENT"
    exit 0
fi

# Ejecutar descarga
python3 "$PROJECT_ROOT/scripts/fetch_real_data/fetch_sigpac_atom.py" \
    --output-dir "$DOWNLOAD_DIR" \
    --provincias "${PROVINCIAS[@]}" \
    --concurrent "$CONCURRENT" \
    2>&1 | tee -a "$LOG_FILE"

# Verificar que se descargó algo
if [ ! -d "$DOWNLOAD_DIR" ] || [ -z "$(find "$DOWNLOAD_DIR" -name '*.gml' -o -name '*.gpkg' 2>/dev/null)" ]; then
    log_error "No se descargaron ficheros SIGPAC"
    exit 1
fi

DOWNLOAD_COUNT=$(find "$DOWNLOAD_DIR" -type f \( -name '*.gml' -o -name '*.gpkg' -o -name '*.shp' \) | wc -l)
log_info "✅ Descarga completada: $DOWNLOAD_COUNT ficheros geográficos"

# ============================================================================
# CARGA A POSTGIS
# ============================================================================

log_info "Cargando datos a PostGIS..."

python3 "$PROJECT_ROOT/scripts/fetch_real_data/load_sigpac_postgis.py" \
    --input-dir "$DOWNLOAD_DIR" \
    2>&1 | tee -a "$LOG_FILE"

# Verificar carga
if command -v psql &> /dev/null; then
    FEATURE_COUNT=$(psql -h "${POSTGRES_HOST:-localhost}" \
        -p "${POSTGRES_PORT:-5432}" \
        -U "${POSTGRES_USER:-terragalicia}" \
        -d "${POSTGRES_DB:-terragalicia}" \
        -t -c "SELECT COUNT(*) FROM public.recintos_sigpac;" 2>/dev/null || echo "0")
    
    if [ "$FEATURE_COUNT" -gt 0 ]; then
        log_info "✅ Carga completada: $FEATURE_COUNT recintos en PostGIS"
    else
        log_warn "⚠️ Carga potencialmente incompleta (0 recintos detectados)"
    fi
fi

# ============================================================================
# BACKUP
# ============================================================================

log_info "Haciendo backup de PostGIS..."

BACKUP_FILE="${BACKUP_DIR}/recintos_sigpac_$(date +%Y%m%d_%H%M%S).dump"

if command -v pg_dump &> /dev/null; then
    pg_dump -h "${POSTGRES_HOST:-localhost}" \
        -p "${POSTGRES_PORT:-5432}" \
        -U "${POSTGRES_USER:-terragalicia}" \
        -d "${POSTGRES_DB:-terragalicia}" \
        -t "public.recintos_sigpac" \
        -Fc \
        -f "$BACKUP_FILE" 2>/dev/null || true
    
    if [ -f "$BACKUP_FILE" ]; then
        SIZE=$(du -h "$BACKUP_FILE" | awk '{print $1}')
        log_info "✅ Backup creado: $BACKUP_FILE ($SIZE)"
    fi
else
    log_warn "⚠️ pg_dump no disponible, skipping backup"
fi

# ============================================================================
# FINALES
# ============================================================================

log_info "Setup completado!"
log_info "Log guardado en: $LOG_FILE"
log_info ""
log_info "Próximos pasos:"
log_info "  1. Verifica que backend conecta a PostGIS:"
log_info "     curl http://localhost:8000/api/v1/sigpac/parcels"
log_info "  2. Visualiza en frontend:"
log_info "     Abre http://localhost"
log_info "  3. Para actualización periódica, ver: scripts/update_sigpac_nightly.sh"
```

---

## Script 2: Actualización Periódica (Nightly/Monthly)

**Archivo:** `scripts/update_sigpac_nightly.sh`

Ejecutar periódicamente (cron) para mantener datos actualizados.

```bash
#!/bin/bash
#
# update_sigpac_nightly.sh
# ========================
# Descarga cambios en ATOM y reimporta a PostGIS
# Programar con cron (p.ej. domingo 3:00 AM)
#
# Uso:
#   bash scripts/update_sigpac_nightly.sh
#
# En crontab:
#   0 3 * * 0 cd /ruta/a/terragalicia && bash scripts/update_sigpac_nightly.sh >> /var/log/sigpac_update.log 2>&1
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOWNLOAD_DIR="${PROJECT_ROOT}/data/sigpac_raw"
BACKUP_DIR="${PROJECT_ROOT}/backups"
ATOM_URL="https://www.fega.gob.es/orig/atomfeed.xml"
LOCK_FILE="/tmp/sigpac_update_$(whoami).lock"
LOG_FILE="${PROJECT_ROOT}/logs/sigpac_update_$(date +%Y%m%d_%H%M%S).log"

mkdir -p "$(dirname "$LOG_FILE")" "$BACKUP_DIR"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Evitar actualizaciones concurrentes
if [ -f "$LOCK_FILE" ]; then
    log "UPDATE ALREADY RUNNING (lock file: $LOCK_FILE)"
    exit 1
fi

trap "rm -f $LOCK_FILE" EXIT
touch "$LOCK_FILE"

log "Starting SIGPAC update..."

# ============================================================================
# DETECTAR CAMBIOS EN ATOM
# ============================================================================

log "Checking for ATOM changes..."

TEMP_ATOM="/tmp/atomfeed_new_$$.xml"

if ! wget -q --timeout=30 "$ATOM_URL" -O "$TEMP_ATOM" 2>&1 | tee -a "$LOG_FILE"; then
    log "ERROR: Failed to download ATOM"
    rm -f "$TEMP_ATOM"
    exit 1
fi

# Comparar checksums
CURRENT_MD5=$(md5sum "${DOWNLOAD_DIR}/atomfeed.xml" 2>/dev/null | awk '{print $1}' || echo "none")
NEW_MD5=$(md5sum "$TEMP_ATOM" | awk '{print $1}')

log "Current MD5: $CURRENT_MD5"
log "New MD5:     $NEW_MD5"

if [ "$CURRENT_MD5" = "$NEW_MD5" ]; then
    log "No changes in ATOM. Exiting."
    rm -f "$TEMP_ATOM"
    exit 0
fi

log "Changes detected. Proceeding with download..."

# ============================================================================
# DESCARGAR DATOS NUEVOS
# ============================================================================

log "Downloading from FEGA ATOM..."

python3 "$PROJECT_ROOT/scripts/fetch_real_data/fetch_sigpac_atom.py" \
    --output-dir "$DOWNLOAD_DIR" \
    --provincias 15 27 32 36 \
    --concurrent 3 \
    2>&1 | tee -a "$LOG_FILE" || {
    log "ERROR: Download failed"
    rm -f "$TEMP_ATOM"
    exit 1
}

# ============================================================================
# RECARGAR A POSTGIS
# ============================================================================

log "Reloading data into PostGIS..."

python3 "$PROJECT_ROOT/scripts/fetch_real_data/load_sigpac_postgis.py" \
    --input-dir "$DOWNLOAD_DIR" \
    2>&1 | tee -a "$LOG_FILE" || {
    log "ERROR: PostGIS load failed"
    rm -f "$TEMP_ATOM"
    exit 1
}

# ============================================================================
# CREAR BACKUP
# ============================================================================

log "Creating backup..."

BACKUP_FILE="${BACKUP_DIR}/recintos_sigpac_$(date +%Y%m%d_%H%M%S).dump"

if command -v pg_dump &> /dev/null; then
    pg_dump -h "${POSTGRES_HOST:-localhost}" \
        -p "${POSTGRES_PORT:-5432}" \
        -U "${POSTGRES_USER:-terragalicia}" \
        -d "${POSTGRES_DB:-terragalicia}" \
        -t "public.recintos_sigpac" \
        -Fc \
        -f "$BACKUP_FILE" 2>&1 | tee -a "$LOG_FILE" || true
    
    if [ -f "$BACKUP_FILE" ]; then
        SIZE=$(du -h "$BACKUP_FILE" | awk '{print $1}')
        log "Backup created: $BACKUP_FILE ($SIZE)"
        
        # Limpiar backups antiguos (mantener últimos 12)
        find "$BACKUP_DIR" -name "recintos_sigpac_*.dump" -type f | \
            sort -r | tail -n +13 | xargs -r rm
    fi
fi

# ============================================================================
# ACTUALIZAR ATOM CACHED
# ============================================================================

log "Updating cached ATOM..."
mkdir -p "$DOWNLOAD_DIR"
cp "$TEMP_ATOM" "${DOWNLOAD_DIR}/atomfeed.xml"

# ============================================================================
# VACIAR CACHE REDIS
# ============================================================================

log "Clearing Redis cache (sigpac:bbox:* keys)..."

if command -v redis-cli &> /dev/null; then
    REDIS_HOST="${REDIS_HOST:-localhost}"
    REDIS_PORT="${REDIS_PORT:-6379}"
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" \
        --eval "$PROJECT_ROOT/scripts/redis_clear_pattern.lua" \
        , "sigpac:bbox:*" 2>&1 | tee -a "$LOG_FILE" || true
fi

# ============================================================================
# FINALIZACIÓN
# ============================================================================

log "SIGPAC update completed successfully!"
log "Log: $LOG_FILE"

# Cleanup
rm -f "$TEMP_ATOM"
```

---

## Script 3: Validación de Datos

**Archivo:** `scripts/validate_sigpac_postgis.py`

```python
#!/usr/bin/env python3
"""
Valida integridad de datos SIGPAC en PostGIS.

Verifica:
- Tabla existe y tiene datos
- Índices están presentes
- Geometrías son válidas
- Campos clave están completos
"""

import sys
import os
from pathlib import Path

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("ERROR: psycopg2 required. Install with: pip install psycopg2-binary")
    sys.exit(1)

# Configuration from environment
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB', 'terragalicia'),
    'user': os.getenv('POSTGRES_USER', 'terragalicia'),
    'password': os.getenv('POSTGRES_PASSWORD', 'terragalicia'),
}

CHECKS = {
    'table_exists': 'SELECT to_regclass(\'public.recintos_sigpac\')',
    'row_count': 'SELECT COUNT(*) FROM public.recintos_sigpac',
    'geom_valid': 'SELECT COUNT(*) FROM public.recintos_sigpac WHERE NOT ST_IsValid(geom)',
    'geom_empty': 'SELECT COUNT(*) FROM public.recintos_sigpac WHERE ST_IsEmpty(geom)',
    'indexes': '''
        SELECT COUNT(*) FROM pg_indexes 
        WHERE tablename = 'recintos_sigpac' 
        AND schemaname = 'public'
    ''',
    'provincia_missing': 'SELECT COUNT(*) FROM public.recintos_sigpac WHERE provincia IS NULL',
    'municipio_missing': 'SELECT COUNT(*) FROM public.recintos_sigpac WHERE municipio IS NULL',
}

def green(text):
    return f"\033[92m{text}\033[0m"

def red(text):
    return f"\033[91m{text}\033[0m"

def yellow(text):
    return f"\033[93m{text}\033[0m"

def main():
    print("Validating SIGPAC PostGIS data...")
    print(f"Database: {DB_CONFIG['database']} @ {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print()
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check 1: Table exists
        cursor.execute(CHECKS['table_exists'])
        result = cursor.fetchone()[0]
        if result:
            print(green("✅ Table recintos_sigpac exists"))
        else:
            print(red("❌ Table recintos_sigpac NOT FOUND"))
            sys.exit(1)
        
        # Check 2: Row count
        cursor.execute(CHECKS['row_count'])
        count = cursor.fetchone()[0]
        if count > 0:
            print(green(f"✅ {count:,} features found"))
        else:
            print(red("❌ Table is empty"))
            sys.exit(1)
        
        # Check 3: Valid geometries
        cursor.execute(CHECKS['geom_valid'])
        invalid = cursor.fetchone()[0]
        if invalid == 0:
            print(green("✅ All geometries are valid"))
        else:
            print(yellow(f"⚠️  {invalid} invalid geometries (use ST_MakeValid() to fix)"))
        
        # Check 4: Empty geometries
        cursor.execute(CHECKS['geom_empty'])
        empty = cursor.fetchone()[0]
        if empty == 0:
            print(green("✅ No empty geometries"))
        else:
            print(yellow(f"⚠️  {empty} empty geometries"))
        
        # Check 5: Indexes
        cursor.execute(CHECKS['indexes'])
        idx_count = cursor.fetchone()[0]
        if idx_count >= 3:  # geom_idx, prov_mun_idx, uso_idx
            print(green(f"✅ {idx_count} indexes found"))
        else:
            print(yellow(f"⚠️  Only {idx_count} indexes (expected 3+)"))
        
        # Check 6: Missing provincia
        cursor.execute(CHECKS['provincia_missing'])
        missing_prov = cursor.fetchone()[0]
        if missing_prov == 0:
            print(green("✅ No missing provincia values"))
        else:
            print(yellow(f"⚠️  {missing_prov} missing provincia values"))
        
        # Check 7: Missing municipio
        cursor.execute(CHECKS['municipio_missing'])
        missing_mun = cursor.fetchone()[0]
        if missing_mun == 0:
            print(green("✅ No missing municipio values"))
        else:
            print(yellow(f"⚠️  {missing_mun} missing municipio values"))
        
        # Statistics
        print()
        print("Summary:")
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT provincia) as provincias,
                COUNT(DISTINCT municipio) as municipios,
                COUNT(DISTINCT uso_sigpac) as usos
            FROM public.recintos_sigpac
        ''')
        total, prov_count, mun_count, uso_count = cursor.fetchone()
        
        print(f"  Total features: {total:,}")
        print(f"  Provinces: {prov_count}")
        print(f"  Municipalities: {mun_count}")
        print(f"  Soil uses: {uso_count}")
        
        cursor.close()
        conn.close()
        
        print()
        print(green("Validation completed successfully!"))
        
    except Exception as e:
        print(red(f"ERROR: {e}"))
        sys.exit(1)

if __name__ == '__main__':
    main()
```

---

## Script 4: Backup & Restore

**Archivo:** `scripts/backup_restore_sigpac.sh`

```bash
#!/bin/bash
#
# backup_restore_sigpac.sh
# ========================
# Crea backups y restaura datos SIGPAC de PostGIS
#
# Uso:
#   bash scripts/backup_restore_sigpac.sh backup               # Crear backup
#   bash scripts/backup_restore_sigpac.sh restore <backup.dump> # Restaurar
#   bash scripts/backup_restore_sigpac.sh list                 # Listar backups
#

BACKUP_DIR="backups"
mkdir -p "$BACKUP_DIR"

case "${1:-list}" in
    backup)
        BACKUP_FILE="${BACKUP_DIR}/recintos_sigpac_$(date +%Y%m%d_%H%M%S).dump"
        echo "Creating backup: $BACKUP_FILE"
        
        pg_dump \
            -h "${POSTGRES_HOST:-localhost}" \
            -p "${POSTGRES_PORT:-5432}" \
            -U "${POSTGRES_USER:-terragalicia}" \
            -d "${POSTGRES_DB:-terragalicia}" \
            -t "public.recintos_sigpac" \
            -Fc \
            -f "$BACKUP_FILE"
        
        SIZE=$(du -h "$BACKUP_FILE" | awk '{print $1}')
        echo "✅ Backup created: $BACKUP_FILE ($SIZE)"
        ;;
    
    restore)
        if [ -z "$2" ]; then
            echo "Usage: $0 restore <backup.dump>"
            exit 1
        fi
        
        BACKUP_FILE="$2"
        
        if [ ! -f "$BACKUP_FILE" ]; then
            echo "Error: Backup file not found: $BACKUP_FILE"
            exit 1
        fi
        
        echo "⚠️  This will OVERWRITE the current recintos_sigpac table"
        read -p "Continue? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Aborted"
            exit 1
        fi
        
        echo "Restoring from: $BACKUP_FILE"
        
        # Drop existing table
        psql \
            -h "${POSTGRES_HOST:-localhost}" \
            -p "${POSTGRES_PORT:-5432}" \
            -U "${POSTGRES_USER:-terragalicia}" \
            -d "${POSTGRES_DB:-terragalicia}" \
            -c "DROP TABLE IF EXISTS public.recintos_sigpac CASCADE"
        
        # Restore
        pg_restore \
            -h "${POSTGRES_HOST:-localhost}" \
            -p "${POSTGRES_PORT:-5432}" \
            -U "${POSTGRES_USER:-terragalicia}" \
            -d "${POSTGRES_DB:-terragalicia}" \
            -v "$BACKUP_FILE"
        
        echo "✅ Restore completed"
        ;;
    
    list)
        echo "Available backups:"
        ls -lh "$BACKUP_DIR"/recintos_sigpac_*.dump 2>/dev/null || echo "  (none)"
        ;;
    
    *)
        echo "Usage: $0 {backup|restore|list}"
        exit 1
        ;;
esac
```

---

## Instalación en Crontab

Para ejecutar actualizaciones automáticamente:

```bash
# Editar crontab
crontab -e

# Agregar línea (actualización cada domingo a las 3 AM):
0 3 * * 0 cd /path/to/terragalicia && bash scripts/update_sigpac_nightly.sh >> /var/log/sigpac_update.log 2>&1

# Verificar cron jobs
crontab -l
```

---

## Testing Manual

```bash
# 1. Setup inicial
bash scripts/setup_sigpac_initial.sh

# 2. Verificar datos
python3 scripts/validate_sigpac_postgis.py

# 3. Consultar desde PostGIS
psql -c "SELECT COUNT(*) FROM public.recintos_sigpac"

# 4. Probar API backend
curl "http://localhost:8000/api/v1/sigpac/parcels?bbox=-9.3,42.7,-7.4,43.8"

# 5. Crear backup
bash scripts/backup_restore_sigpac.sh backup

# 6. Listar backups
bash scripts/backup_restore_sigpac.sh list

# 7. Consultar municipios específicos
psql << 'EOF'
SELECT COUNT(*), provincia, municipio 
FROM public.recintos_sigpac 
GROUP BY provincia, municipio 
ORDER BY provincia, municipio;
EOF
```

---

**Próximo paso:** Implementar estos scripts en el proyecto y probar con datos reales.

