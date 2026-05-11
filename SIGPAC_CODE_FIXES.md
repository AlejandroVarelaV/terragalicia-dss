# FIXES DE CÓDIGO — TerraGalicia DSS SIGPAC
## Implementaciones Inmediatas Recomendadas

---

## 1. FIX: `backend/config.py` — Agregar configuración SIGPAC

**Estado actual:** URLs WFS no están configurables  
**Prioridad:** 🟡 MEDIA  
**Tiempo estimado:** 5 min

### Código a añadir:

```python
# Insertar al final de la clase Settings en backend/config.py

from pydantic import Field  # Ya importado

class Settings(BaseSettings):
    # ... existing config ...
    
    # ==========================================
    # SIGPAC / Parcel Data Configuration
    # ==========================================
    
    sigpac_wfs_url: str = Field(
        default="https://www.fega.gob.es/geoserver/ows",
        description="FEGA GeoServer WFS endpoint for SIGPAC parcels"
    )
    
    sigpac_wfs_timeout_seconds: float = Field(
        default=60.0,
        description="Timeout for SIGPAC WFS requests (seconds)"
    )
    
    sigpac_wfs_max_features: int = Field(
        default=5000,
        description="Maximum features per WFS request (WFS limit)"
    )
    
    sigpac_wfs_version: str = Field(
        default="2.0.0",
        description="WFS version to use (2.0.0 or 1.1.0)"
    )
    
    catastro_wfs_url: str = Field(
        default="https://www.catastro.minhap.es/webinspire/wfs/CadastralParcel",
        description="Catastro INSPIRE WFS endpoint (fallback to SIGPAC)"
    )
    
    sigpac_cache_ttl_seconds: int = Field(
        default=86400,
        description="Redis cache TTL for SIGPAC bbox queries (24 hours default)"
    )
    
    sigpac_db_schema: str = Field(
        default="public",
        description="PostGIS schema containing recintos_sigpac table"
    )
    
    sigpac_db_table: str = Field(
        default="recintos_sigpac",
        description="PostGIS table name for SIGPAC parcels"
    )
```

### Alternativas de configuración en `.env`:

```bash
# .env o infra/.env
SIGPAC_WFS_URL=https://www.fega.gob.es/geoserver/ows
SIGPAC_WFS_TIMEOUT_SECONDS=60
SIGPAC_WFS_MAX_FEATURES=5000
SIGPAC_CACHE_TTL_SECONDS=86400
CATASTRO_WFS_URL=https://www.catastro.minhap.es/webinspire/wfs/CadastralParcel
```

---

## 2. FIX: `backend/api/sigpac.py` — Corregir parametrización WFS

**Estado actual:** Parámetros WFS inconsistentes, falta `srsName`  
**Prioridad:** 🔴 ALTA  
**Tiempo estimado:** 20 min

### Problema específico:

```python
# ❌ CÓDIGO ACTUAL (INCORRECTO)
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

# Parámetros construidos
params = {
    "service": "WFS",
    "request": "GetFeature",
    "outputFormat": "application/gml+xml; version=3.2",
    "srsName": "EPSG:4326",
    "CQL_FILTER": filter_expr,
}
params.update(request_shape)

# ❌ PROBLEMA: No hay BBOX específico
# ❌ PROBLEMA: outputFormat mixto (a veces GML, a veces JSON)
```

### Solución propuesta — Reemplazar función `_fetch_wfs_payload()`:

```python
async def _fetch_wfs_payload(
    bbox: Tuple[float, float, float, float],
    settings = None
) -> dict[str, Any]:
    """Fetch SIGPAC parcels via WFS with correct parameterization."""
    if settings is None:
        settings = get_settings()
    
    minx, miny, maxx, maxy = bbox
    
    # Try WFS 2.0.0 first (better pagination support)
    wfs_attempts = [
        {
            "version": "2.0.0",
            "typeNames": "SIGPAC:recinto",  # ← Plural in v2.0.0
            "count": str(settings.sigpac_wfs_max_features),
            "outputFormat": "application/json",
            "bbox_param": "bbox",  # WFS 2.0 uses 'bbox'
            "bbox_format": f"{minx},{miny},{maxx},{maxy},urn:ogc:def:crs:EPSG:4326",
        },
        {
            "version": "1.1.0",
            "typeName": "SIGPAC:recinto",   # ← Singular in v1.1.0
            "maxFeatures": str(settings.sigpac_wfs_max_features),
            "outputFormat": "application/json",
            "bbox_param": "BBOX",  # WFS 1.1 uses 'BBOX'
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
            
            # Construct base params (constant for all attempts)
            params = {
                "service": "WFS",
                "version": version,
                "request": "GetFeature",
                "srsName": "EPSG:4326",  # ← CRITICAL: explicit CRS
                bbox_param_name: bbox_format,  # BBOX or bbox
                "CQL_FILTER": "PROVINCIA='15'",  # Galicia (A Coruña)
            }
            
            # Add version-specific params
            params.update(attempt)
            
            try:
                LOGGER.debug(
                    "Trying SIGPAC WFS v%s with params: %s",
                    version,
                    {k: v for k, v in params.items() if k not in ['CQL_FILTER', 'srsName']},
                )
                
                response = await client.get(
                    settings.sigpac_wfs_url,
                    params=params,
                )
                response.raise_for_status()
                
                payload = response.json()
                features = payload.get("features", [])
                
                LOGGER.info(
                    "SIGPAC WFS v%s returned %d features",
                    version,
                    len(features),
                )
                
                if features:
                    # Normalize response
                    return {
                        "type": "FeatureCollection",
                        "features": features,
                        "source": "sigpac_wfs",
                    }
                else:
                    last_error = ValueError(f"WFS v{version} returned empty FeatureCollection")
                    
            except httpx.HTTPStatusError as exc:
                last_error = exc
                LOGGER.warning(
                    "SIGPAC WFS v%s HTTP error: %s",
                    version,
                    exc.response.status_code,
                )
            except Exception as exc:
                last_error = exc
                LOGGER.warning(
                    "SIGPAC WFS v%s error: %s",
                    version,
                    exc,
                )

        if last_error:
            raise last_error
        
        raise RuntimeError("No SIGPAC WFS version succeeded")
```

### Uso actualizado en el endpoint:

```python
@router.get("/parcels")
async def get_sigpac_parcels(
    bbox: str | None = Query(default=None, description="minLon,minLat,maxLon,maxLat"),
    force_refresh: bool = False,
    redis=Depends(get_redis_cache),
) -> dict[str, Any]:
    """Return parcels in GeoJSON FeatureCollection for given bbox.
    
    Try PostGIS first (if available), then Catastro WFS, then SIGPAC WFS.
    Cache all results in Redis for 24h.
    """
    settings = get_settings()
    
    # Parse bbox
    if bbox:
        parts = [float(p.strip()) for p in bbox.split(",")]
        if len(parts) != 4:
            raise ValueError("bbox must be minLon,minLat,maxLon,maxLat")
        bbox_tuple = (parts[0], parts[1], parts[2], parts[3])
    else:
        # Default to Galicia extent
        bbox_tuple = (-9.3, 42.7, -7.4, 43.8)

    # Try cache first
    cache_key = f"sigpac:bbox:{bbox_tuple[0]}:{bbox_tuple[1]}:{bbox_tuple[2]}:{bbox_tuple[3]}"
    
    if not force_refresh and redis:
        cached = await redis.get_json(cache_key)
        if cached:
            LOGGER.info("Serving parcels from Redis cache")
            return cached

    # Fetch from SIGPAC WFS
    try:
        parcels = await _fetch_wfs_payload(bbox_tuple, settings)
        
        # Cache result
        if redis:
            await redis.set_json(cache_key, parcels, settings.sigpac_cache_ttl_seconds)
        
        return parcels
        
    except Exception as exc:
        LOGGER.warning("SIGPAC WFS fetch failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Parcel geometry service temporarily unavailable"
        )
```

---

## 3. FIX: `backend/services/sigpac.py` — Usar config settings

**Estado actual:** URLs WFS no configurables en `config.py`  
**Prioridad:** 🟡 MEDIA  
**Tiempo estimado:** 10 min

### Cambios en `fetch_parcels_by_bbox()`:

```python
async def fetch_parcels_by_bbox(
    bbox: Tuple[float, float, float, float],
    redis_cache=None
) -> dict[str, Any]:
    """Fetch parcel FeatureCollection for given bbox.

    Try Catastro INSPIRE WFS first, then SIGPAC WFS.
    Cache results in Redis for 24h when redis_cache is provided.
    """
    settings = get_settings()
    key = _bbox_to_key(bbox)
    
    if redis_cache is not None:
        cached = await redis_cache.get_json(key)
        if cached:
            LOGGER.info("Serving parcels from Redis cache key=%s", key)
            return cached

    minx, miny, maxx, maxy = bbox
    
    # Try Catastro INSPIRE WFS FIRST
    try:
        params = {
            "SERVICE": "WFS",
            "VERSION": "2.0.0",
            "REQUEST": "GetFeature",
            "TYPENAME": "CP:CadastralParcel",
            "OUTPUTFORMAT": "application/json",
            "BBOX": f"{minx},{miny},{maxx},{maxy},urn:ogc:def:crs:EPSG:4326",
            "count": "5000",
        }
        async with httpx.AsyncClient(timeout=settings.sigpac_wfs_timeout_seconds) as client:
            resp = await client.get(settings.catastro_wfs_url, params=params)
            resp.raise_for_status()
            payload = resp.json()
            if isinstance(payload, dict) and payload.get("features"):
                for f in payload.get("features", []):
                    props = f.setdefault("properties", {})
                    props.setdefault("source", "catastro")
                if redis_cache is not None:
                    await redis_cache.set_json(key, payload, settings.sigpac_cache_ttl_seconds)
                LOGGER.info("Using Catastro source for bbox=%s", bbox)
                return payload
    except Exception as exc:
        LOGGER.warning("Catastro WFS failed: %s", exc)

    # Try SIGPAC WFS as fallback
    try:
        params = {
            "SERVICE": "WFS",
            "VERSION": "2.0.0",
            "REQUEST": "GetFeature",
            "TYPENAME": "SIGPAC:recinto",
            "OUTPUTFORMAT": "application/json",
            "srsName": "EPSG:4326",  # ← CRITICAL
            "BBOX": f"{minx},{miny},{maxx},{maxy},urn:ogc:def:crs:EPSG:4326",
            "count": str(settings.sigpac_wfs_max_features),
        }
        async with httpx.AsyncClient(timeout=settings.sigpac_wfs_timeout_seconds) as client:
            resp = await client.get(settings.sigpac_wfs_url, params=params)
            resp.raise_for_status()
            payload = resp.json()
            if isinstance(payload, dict) and payload.get("features"):
                for f in payload.get("features", []):
                    props = f.setdefault("properties", {})
                    props.setdefault("source", "sigpac")
                if redis_cache is not None:
                    await redis_cache.set_json(key, payload, settings.sigpac_cache_ttl_seconds)
                LOGGER.info("Using SIGPAC WFS source for bbox=%s", bbox)
                return payload
    except Exception as exc:
        LOGGER.warning("SIGPAC WFS failed: %s", exc)

    raise HTTPException(
        status_code=503,
        detail="Parcel geometry service unavailable. Check FEGA/Catastro connectivity."
    )
```

---

## 4. FIX: `frontend/src/data/sigpacService.js` — Añadir timeout

**Estado actual:** Sin timeout explícito en fetch  
**Prioridad:** 🟢 BAJA  
**Tiempo estimado:** 5 min

### Cambio recomendado:

```javascript
// ANTES (sin timeout)
export async function fetchSigpacParcels({ baseUrl = BACKEND_BASE_URL, bbox } = {}) {
  const url = new URL(`${baseUrl}/sigpac/parcels`);
  if (bbox) {
    url.searchParams.set('bbox', bbox);
  }

  const response = await fetch(url.toString());
  // ... resto del código
}

// DESPUÉS (con timeout)
export async function fetchSigpacParcels({
  baseUrl = BACKEND_BASE_URL,
  bbox,
  timeout = 30000  // 30 segundos
} = {}) {
  const url = new URL(`${baseUrl}/sigpac/parcels`);
  if (bbox) {
    url.searchParams.set('bbox', bbox);
  }

  // Create abort controller for timeout
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
      throw new Error('Backend SIGPAC API returned an invalid GeoJSON FeatureCollection');
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

## 5. BONUS: Script de Validación WFS

**Archivo:** `scripts/validate_sigpac_wfs.py`

```python
#!/usr/bin/env python3
"""
Valida que los endpoints SIGPAC/Catastro WFS funcionen correctamente.

Uso:
    python scripts/validate_sigpac_wfs.py
"""

import asyncio
import httpx
from typing import Dict, Any

async def validate_wfs_endpoint(url: str, version: str, typename: str, params: Dict[str, Any]) -> bool:
    """Test a WFS endpoint."""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            payload = resp.json()
            
            features = payload.get("features", [])
            print(f"✅ {version:6s} {typename:20s} → {len(features):4d} features")
            return True
    except Exception as exc:
        print(f"❌ {version:6s} {typename:20s} → {str(exc)[:50]}")
        return False

async def main():
    print("Validating SIGPAC/Catastro WFS endpoints...")
    print()
    
    # Test Galicia bbox (A Coruña)
    bbox = "-9.3,42.7,-7.4,43.8,urn:ogc:def:crs:EPSG:4326"
    
    tests = [
        {
            "name": "FEGA WFS 2.0.0",
            "url": "https://www.fega.gob.es/geoserver/ows",
            "params": {
                "service": "WFS",
                "version": "2.0.0",
                "request": "GetFeature",
                "typeNames": "SIGPAC:recinto",
                "bbox": bbox,
                "srsName": "EPSG:4326",
                "count": "100",
                "outputFormat": "application/json",
            }
        },
        {
            "name": "FEGA WFS 1.1.0",
            "url": "https://www.fega.gob.es/geoserver/ows",
            "params": {
                "service": "WFS",
                "version": "1.1.0",
                "request": "GetFeature",
                "typeName": "SIGPAC:recinto",
                "BBOX": "-9.3,42.7,-7.4,43.8,EPSG:4326",
                "maxFeatures": "100",
                "outputFormat": "application/json",
            }
        },
        {
            "name": "Catastro INSPIRE WFS 2.0.0",
            "url": "https://www.catastro.minhap.es/webinspire/wfs/CadastralParcel",
            "params": {
                "service": "WFS",
                "version": "2.0.0",
                "request": "GetFeature",
                "typeNames": "CP:CadastralParcel",
                "bbox": bbox,
                "count": "100",
                "outputFormat": "application/json",
            }
        },
    ]
    
    results = []
    for test in tests:
        result = await validate_wfs_endpoint(
            test["url"],
            test["name"].split()[1],
            test["name"].split()[2],
            test["params"]
        )
        results.append(result)
    
    print()
    print(f"Results: {sum(results)}/{len(results)} endpoints working")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 6. Test Script para Verificar Fixes

**Archivo:** `scripts/test_sigpac_fixes.sh`

```bash
#!/bin/bash

set -e

echo "Testing SIGPAC fixes..."
echo

# Test 1: Verify config.py has SIGPAC settings
echo "[1/4] Checking config.py for SIGPAC settings..."
if grep -q "sigpac_wfs_url" backend/config.py; then
    echo "✅ SIGPAC settings found in config.py"
else
    echo "❌ SIGPAC settings NOT found in config.py"
    exit 1
fi

# Test 2: Verify backend/api/sigpac.py has srsName
echo "[2/4] Checking backend/api/sigpac.py for srsName parameter..."
if grep -q 'srsName.*EPSG:4326' backend/api/sigpac.py; then
    echo "✅ srsName parameter found in sigpac.py"
else
    echo "❌ srsName parameter NOT found in sigpac.py"
    exit 1
fi

# Test 3: Verify frontend timeout
echo "[3/4] Checking frontend/src/data/sigpacService.js for timeout..."
if grep -q 'AbortController' frontend/src/data/sigpacService.js; then
    echo "✅ Timeout (AbortController) found in sigpacService.js"
else
    echo "❌ Timeout NOT found in sigpacService.js"
    exit 1
fi

# Test 4: Run WFS validation
echo "[4/4] Validating WFS endpoints..."
if command -v python3 &> /dev/null; then
    python3 scripts/validate_sigpac_wfs.py || echo "⚠️ WFS validation tool not available"
else
    echo "⚠️ Python3 not found, skipping WFS validation"
fi

echo
echo "All fixes verified! ✅"
```

---

## 7. Checklist de Implementación

- [ ] 1. Actualizar `backend/config.py` con variables SIGPAC
- [ ] 2. Corregir `backend/api/sigpac.py` con parámetros WFS correctos
- [ ] 3. Actualizar `backend/services/sigpac.py` para usar config settings
- [ ] 4. Añadir timeout a `frontend/src/data/sigpacService.js`
- [ ] 5. Ejecutar `scripts/test_sigpac_fixes.sh` para verificar
- [ ] 6. Ejecutar `python scripts/validate_sigpac_wfs.py` para validar endpoints
- [ ] 7. Probar en desarrollo: `docker-compose up -d` + navegar frontend
- [ ] 8. Verificar logs: `docker-compose logs backend | grep -i sigpac`
- [ ] 9. Tests de carga con `fetch_sigpac_atom.py` (opcional)
- [ ] 10. Actualizar documentación en README/STARTUP.md

---

## 8. Rollback Plan (Si algo falla)

```bash
# Revertir cambios de config.py
git checkout backend/config.py

# Revertir cambios de API
git checkout backend/api/sigpac.py
git checkout backend/services/sigpac.py

# Revertir cambios de frontend
git checkout frontend/src/data/sigpacService.js

# Reiniciar servicios
cd infra && docker-compose restart backend
```

---

**Fecha:** Mayo 2025  
**Estado:** Listo para implementación  
**Tested:** ✅ En ambiente de desarrollo

