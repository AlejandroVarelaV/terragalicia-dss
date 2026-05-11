# QUICK REFERENCE — SIGPAC Endpoints & Fixes
## TerraGalicia DSS — Copia y Pega

---

## 🚀 Endpoints WFS Correctos (Copiar)

### FEGA GeoServer (SIGPAC recinto)

**WFS 2.0.0:**
```http
GET https://www.fega.gob.es/geoserver/ows?
    service=WFS&
    version=2.0.0&
    request=GetFeature&
    typeNames=SIGPAC:recinto&
    outputFormat=application/json&
    srsName=EPSG:4326&
    CQL_FILTER=PROVINCIA='15'&
    count=5000
```

**WFS 1.1.0:**
```http
GET https://www.fega.gob.es/geoserver/ows?
    service=WFS&
    version=1.1.0&
    request=GetFeature&
    typeName=SIGPAC:recinto&
    outputFormat=application/json&
    srsName=EPSG:4326&
    BBOX=-9.3,42.7,-7.4,43.8,EPSG:4326&
    maxFeatures=5000
```

### Catastro INSPIRE (fallback)

```http
GET https://www.catastro.minhap.es/webinspire/wfs/CadastralParcel?
    service=WFS&
    version=2.0.0&
    request=GetFeature&
    typeNames=CP:CadastralParcel&
    outputFormat=application/json&
    bbox=-9.3,42.7,-7.4,43.8,urn:ogc:def:crs:EPSG:4326&
    count=5000
```

### FEGA ATOM (descarga masiva)

```
Raíz: https://www.fega.gob.es/orig/atomfeed.xml
A Coruña (15): https://www.fega.gob.es/orig/atomfeed_15.xml
Lugo (27): https://www.fega.gob.es/orig/atomfeed_27.xml
Ourense (32): https://www.fega.gob.es/orig/atomfeed_32.xml
Pontevedra (36): https://www.fega.gob.es/orig/atomfeed_36.xml
```

---

## 🔧 FIX #2: `backend/api/sigpac.py` (CRÍTICO)

**Buscar/Reemplazar:**

```python
# ❌ ANTES (INCORRECTO)
async def _fetch_wfs_payload() -> dict[str, Any]:
    requests_to_try = [
        {
            "version": "2.0.0",
            "typeNames": "SIGPAC:recinto",
            "count": "5000",
        },
        {
            "version": "1.1.0",
            "typeName": "SIGPAC:recinto",
            "maxFeatures": "5000",
        },
    ]

    filter_expr = "PROVINCIA='15'"

    timeout = httpx.Timeout(60.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        last_error: Exception | None = None
        for endpoint in SIGPAC_ENDPOINTS:
            for request_shape in requests_to_try:
                params = {
                    "service": "WFS",
                    "request": "GetFeature",
                    "outputFormat": "application/gml+xml; version=3.2",
                    "srsName": "EPSG:4326",
                    "CQL_FILTER": filter_expr,
                }
                params.update(request_shape)
                # ❌ PROBLEMA: No hay BBOX explícito
                # ❌ PROBLEMA: outputFormat mixto


# ✅ DESPUÉS (CORRECTO)
async def _fetch_wfs_payload(bbox: Tuple[float, float, float, float], settings=None) -> dict[str, Any]:
    if settings is None:
        settings = get_settings()
    
    minx, miny, maxx, maxy = bbox
    
    wfs_attempts = [
        {
            "version": "2.0.0",
            "typeNames": "SIGPAC:recinto",  # Plural en v2.0
            "count": str(settings.sigpac_wfs_max_features),
            "outputFormat": "application/json",
            "bbox_param": "bbox",
            "bbox_format": f"{minx},{miny},{maxx},{maxy},urn:ogc:def:crs:EPSG:4326",
        },
        {
            "version": "1.1.0",
            "typeName": "SIGPAC:recinto",   # Singular en v1.1
            "maxFeatures": str(settings.sigpac_wfs_max_features),
            "outputFormat": "application/json",
            "bbox_param": "BBOX",
            "bbox_format": f"{minx},{miny},{maxx},{maxy},EPSG:4326",
        },
    ]

    timeout = httpx.Timeout(settings.sigpac_wfs_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout) as client:
        last_error: Exception | None = None
        
        for attempt in wfs_attempts:
            version = attempt.pop("version")
            bbox_param_name = attempt.pop("bbox_param")
            bbox_format = attempt.pop("bbox_format")
            
            params = {
                "service": "WFS",
                "version": version,
                "request": "GetFeature",
                "srsName": "EPSG:4326",  # ✅ CRÍTICO
                bbox_param_name: bbox_format,  # ✅ BBOX explícito
            }
            params.update(attempt)
            
            try:
                response = await client.get(settings.sigpac_wfs_url, params=params)
                response.raise_for_status()
                payload = response.json()
                features = payload.get("features", [])
                
                if features:
                    return {
                        "type": "FeatureCollection",
                        "features": features,
                        "source": "sigpac_wfs",
                    }
                    
            except Exception as exc:
                last_error = exc
                LOGGER.warning("WFS v%s error: %s", version, exc)

        if last_error:
            raise last_error
        raise RuntimeError("No SIGPAC WFS version succeeded")
```

---

## 🔧 FIX #1: `backend/config.py` (Añadir)

```python
# Insertar en la clase Settings:

sigpac_wfs_url: str = Field(
    default="https://www.fega.gob.es/geoserver/ows",
    description="FEGA GeoServer WFS endpoint"
)

sigpac_wfs_timeout_seconds: float = Field(
    default=60.0,
    description="WFS request timeout (seconds)"
)

sigpac_wfs_max_features: int = Field(
    default=5000,
    description="Max features per WFS request"
)

sigpac_wfs_version: str = Field(
    default="2.0.0",
    description="WFS version (2.0.0 or 1.1.0)"
)

catastro_wfs_url: str = Field(
    default="https://www.catastro.minhap.es/webinspire/wfs/CadastralParcel",
    description="Catastro INSPIRE WFS endpoint"
)

sigpac_cache_ttl_seconds: int = Field(
    default=86400,
    description="Redis cache TTL for SIGPAC (24h)"
)
```

---

## 🔧 FIX #4: `frontend/src/data/sigpacService.js` (Timeout)

```javascript
// ANTES
export async function fetchSigpacParcels({ baseUrl = BACKEND_BASE_URL, bbox } = {}) {
  const url = new URL(`${baseUrl}/sigpac/parcels`);
  if (bbox) {
    url.searchParams.set('bbox', bbox);
  }
  const response = await fetch(url.toString());
  // ...
}

// DESPUÉS (con timeout)
export async function fetchSigpacParcels({
  baseUrl = BACKEND_BASE_URL,
  bbox,
  timeout = 30000
} = {}) {
  const url = new URL(`${baseUrl}/sigpac/parcels`);
  if (bbox) {
    url.searchParams.set('bbox', bbox);
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url.toString(), {
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`Backend SIGPAC API failed with HTTP ${response.status}`);
    }

    const payload = await response.json();
    if (payload?.type !== 'FeatureCollection' || !Array.isArray(payload?.features)) {
      throw new Error('Invalid GeoJSON FeatureCollection');
    }

    return payload;
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new Error(`SIGPAC request timeout after ${timeout}ms`);
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}
```

---

## 📋 Comandos para Ejecutar

```bash
# 1. Setup inicial (90 min)
bash scripts/setup_sigpac_initial.sh

# 2. Validar datos
python3 scripts/validate_sigpac_postgis.py

# 3. Test API
curl "http://localhost:8000/api/v1/sigpac/parcels?bbox=-9.3,42.7,-7.4,43.8"

# 4. Crear backup
bash scripts/backup_restore_sigpac.sh backup

# 5. Listar backups
bash scripts/backup_restore_sigpac.sh list

# 6. Restaurar (si algo falla)
bash scripts/backup_restore_sigpac.sh restore backups/recintos_sigpac_YYYYMMDD.dump

# 7. Configurar cron (actualización automática)
crontab -e
# Agregar: 0 3 * * 0 cd /path/to/terragalicia && bash scripts/update_sigpac_nightly.sh

# 8. Ver logs
tail -f logs/sigpac_*.log
```

---

## 🧪 Tests de Validación

```bash
# ✅ Test WFS endpoints
python3 scripts/validate_sigpac_wfs.py

# ✅ Test código fixes
bash scripts/test_sigpac_fixes.sh

# ✅ Test PostGIS
python3 scripts/validate_sigpac_postgis.py

# ✅ Test API
curl -v "http://localhost:8000/api/v1/sigpac/parcels"

# ✅ Test Redis cache
redis-cli get "sigpac:bbox:*"

# ✅ Test geometrías PostGIS
psql -c "SELECT COUNT(*) FROM public.recintos_sigpac WHERE NOT ST_IsValid(geom);"
```

---

## 📊 Códigos de Provincia Galicia

```
15 — A Coruña (La Coruña)
27 — Lugo
32 — Ourense (Orense)
36 — Pontevedra
```

**Uso en scripts:**
```bash
bash scripts/setup_sigpac_initial.sh --provincias 15 36  # Solo Coruña + Pontevedra
```

---

## 🚨 Troubleshooting Rápido

| Problema | Solución |
|----------|----------|
| `HTTP 503 FEGA WFS` | Ya maneja reintentos. Esperar o usar PostGIS |
| `srsName no reconocido` | Cambiar `srsName` a `srsName` (minúscula) o probar v1.1.0 |
| `Features truncados` | WFS limita a 5000. Usar ATOM para descarga masiva |
| `Geometrías inválidas` | ogr2ogr maneja con `-dim XY -nlt PROMOTE_TO_MULTI` |
| `PostGIS vacío` | Ejecutar `bash scripts/setup_sigpac_initial.sh` |
| `Caché Redis no funciona` | Verificar Redis está corriendo: `redis-cli ping` |
| `Datos desactualizados` | Ejecutar `bash scripts/update_sigpac_nightly.sh` |
| `Restaurar de backup` | `bash scripts/backup_restore_sigpac.sh restore <file.dump>` |

---

## 🔗 URLs Clave

```
FEGA ATOM (descarga):      https://www.fega.gob.es/orig/atomfeed.xml
FEGA WFS (queries):        https://www.fega.gob.es/geoserver/ows
Catastro INSPIRE WFS:      https://www.catastro.minhap.es/webinspire/wfs/CadastralParcel

Backend API (local):       http://localhost:8000/api/v1/sigpac/parcels
Documentación:             http://localhost:8000/api/v1/docs

Redis (local):             http://localhost:6379
PostGIS (local):           postgresql://localhost:5432/terragalicia
```

---

## 📝 Parametrización de Ejemplo

### Galicia completa (toda la región)

```python
bbox = (-9.3, 42.7, -7.4, 43.8)  # minLon, minLat, maxLon, maxLat
```

### A Coruña (provincia 15)

```python
bbox = (-8.8, 43.3, -8.0, 43.8)
```

### Pontevedra (provincia 36)

```python
bbox = (-8.9, 42.2, -8.4, 42.9)
```

### Lugo (provincia 27)

```python
bbox = (-8.4, 42.8, -7.3, 43.4)
```

### Ourense (provincia 32)

```python
bbox = (-8.2, 41.8, -6.8, 42.8)
```

---

## ✅ Checklist ANTES de Producción

- [ ] FIX #2 (`backend/api/sigpac.py`) implementado
- [ ] `grep "srsName" backend/api/sigpac.py` devuelve resultados
- [ ] `bash scripts/test_sigpac_fixes.sh` pasa
- [ ] `python3 scripts/validate_sigpac_postgis.py` sin errores críticos
- [ ] `curl http://localhost:8000/api/v1/sigpac/parcels` devuelve features
- [ ] Backup creado: `bash scripts/backup_restore_sigpac.sh backup`
- [ ] Cron configurado: `crontab -l | grep sigpac`
- [ ] README actualizado con instrucciones SIGPAC

---

**Estado:** 🟢 LISTO PARA COPIAR Y PEGAR

Ver documentación completa en:
- [SIGPAC_EXECUTIVE_SUMMARY.md](SIGPAC_EXECUTIVE_SUMMARY.md)
- [SIGPAC_CODE_FIXES.md](SIGPAC_CODE_FIXES.md)
- [SIGPAC_IMPLEMENTATION_SCRIPTS.md](SIGPAC_IMPLEMENTATION_SCRIPTS.md)

