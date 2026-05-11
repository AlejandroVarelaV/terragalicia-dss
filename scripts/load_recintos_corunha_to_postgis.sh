#!/usr/bin/env bash
set -euo pipefail

# Usage: export PGHOST PGPORT PGUSER PGPASSWORD PGDATABASE
# or set PG_CONN="host=... user=... dbname=... password=..."

PG_CONN=${PG_CONN:-}
if [ -z "$PG_CONN" ]; then
  : "PG_CONN not set, constructing from env vars"
  : "Ensure PGHOST PGPORT PGUSER PGPASSWORD PGDATABASE are set"
  if [ -z "${PGHOST:-}" ] || [ -z "${PGUSER:-}" ] || [ -z "${PGDATABASE:-}" ]; then
    echo "Set PG_CONN or PGHOST/PGUSER/PGDATABASE (and PGPASSWORD)" >&2
    exit 1
  fi
  PG_CONN="host=${PGHOST} port=${PGPORT:-5432} user=${PGUSER} dbname=${PGDATABASE} password=${PGPASSWORD:-}"
fi

DATA_DIR="Recintos_Corunha"
TABLE="public.recintos_sigpac"

if ! command -v ogr2ogr >/dev/null 2>&1; then
  echo "ogr2ogr not found. Install gdal (gdal-bin) before running this script." >&2
  exit 1
fi

if ! command -v sqlite3 >/dev/null 2>&1; then
  echo "sqlite3 not found. Install sqlite3 before running this script." >&2
  exit 1
fi

echo "Creating target table if not exists..."
psql "${PG_CONN}" -v ON_ERROR_STOP=1 <<'SQL'
CREATE TABLE IF NOT EXISTS public.recintos_sigpac (
  gid serial PRIMARY KEY,
  dn_oid text,
  provincia text,
  municipio text,
  agregado text,
  zona text,
  poligono text,
  parcela text,
  recinto text,
  dn_surface numeric,
  pendiente_media numeric,
  altitud numeric,
  csp text,
  coef_regadio text,
  uso_sigpac text,
  incidencias text,
  region text,
  geom geometry(MULTIPOLYGON,4326)
);
CREATE INDEX IF NOT EXISTS recintos_sigpac_geom_gist ON public.recintos_sigpac USING GIST (geom);
CREATE INDEX IF NOT EXISTS recintos_sigpac_munic_idx ON public.recintos_sigpac (municipio);
CREATE TABLE IF NOT EXISTS public.recintos_loads (
  id serial PRIMARY KEY,
  source_file text,
  features_loaded integer,
  loaded_at timestamptz default now()
);
SQL

echo "Starting batch load from ${DATA_DIR} into ${TABLE}"

shopt -s nullglob
for f in "${DATA_DIR}"/*.gpkg; do
  echo "Processing: $f"
  # detect srs_id from gpkg_contents
  srs_id=$(sqlite3 "$f" "SELECT srs_id FROM gpkg_contents WHERE table_name='recinto' LIMIT 1;" || true)
  if [ -z "$srs_id" ]; then
    echo "Could not detect srs_id for $f, assuming 4258" >&2
    srs_id=4258
  fi
  src_srs="EPSG:${srs_id}"

  # run ogr2ogr: promote to multi, transform to 4326, rename geometry to geom, append
  ogr2ogr \
    -f "PostgreSQL" "PG:${PG_CONN}" \
    "$f" \
    -nln "${TABLE}" \
    -nlt PROMOTE_TO_MULTI \
    -lco GEOMETRY_NAME=geom \
    -lco FID=gid \
    -s_srs "$src_srs" \
    -t_srs "EPSG:4326" \
    -append \
    -skipfailures \
    -progress

  # count inserted features for this file (best-effort: try to get count from gpkg then record)
  cnt=$(sqlite3 "$f" "SELECT COUNT(*) FROM recinto;" || echo 0)
  psql "${PG_CONN}" -v ON_ERROR_STOP=1 -c "INSERT INTO public.recintos_loads (source_file, features_loaded) VALUES ('$(basename "$f")', ${cnt});"
  echo "Loaded ${cnt} features from $(basename "$f")"
done

echo "Post-load deduplication: removing duplicates by dn_oid (keep lowest gid)"
psql "${PG_CONN}" -v ON_ERROR_STOP=1 <<'SQL'
DELETE FROM public.recintos_sigpac a USING public.recintos_sigpac b
WHERE a.dn_oid = b.dn_oid AND a.gid > b.gid;
ANALYZE public.recintos_sigpac;
SQL

echo "Load complete. See table public.recintos_loads for per-file counts."
