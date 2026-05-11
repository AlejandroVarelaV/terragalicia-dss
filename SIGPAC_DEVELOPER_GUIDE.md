# ÍNDICE DE DOCUMENTACIÓN — Auditoría SIGPAC TerraGalicia DSS
## Guía de Navegación Completa

**Generado:** Mayo 2025  
**Documentos:** 4 archivos (25,000+ palabras)  
**Tiempo lectura:** Depende del rol (ver tabla abajo)

---

## 📋 Archivos Generados

```
practica_2/
├── SIGPAC_EXECUTIVE_SUMMARY.md            ← EMPIEZA AQUÍ (2 min)
├── SIGPAC_AUDIT_AND_RECOMMENDATIONS.md    ← Análisis técnico (30 min)
├── SIGPAC_CODE_FIXES.md                   ← Implementación (20 min)
├── SIGPAC_IMPLEMENTATION_SCRIPTS.md       ← Scripts listos (10 min)
└── SIGPAC_DEVELOPER_GUIDE.md              ← Este archivo
```

---

## 👥 Guía por Rol

### 🎯 Desarrollador/Arquitecto

**Ruta de lectura recomendada (1.5 horas):**

1. **10 min:** [SIGPAC_EXECUTIVE_SUMMARY.md](SIGPAC_EXECUTIVE_SUMMARY.md)
   - Entiende el problema y solución
   - Revisa checklist de implementación

2. **20 min:** [SIGPAC_AUDIT_AND_RECOMMENDATIONS.md](SIGPAC_AUDIT_AND_RECOMMENDATIONS.md) — Secciones:
   - 1.1-1.6: Auditoría de código (línea a línea)
   - 2.1-2.6: Fuentes de datos oficiales
   - 3: Comparativa de endpoints
   - 6: Arquitectura recomendada

3. **30 min:** [SIGPAC_CODE_FIXES.md](SIGPAC_CODE_FIXES.md)
   - FIX #2 (crítico): `backend/api/sigpac.py`
   - FIX #1, #3, #4 (complementarios)
   - Scripts de validación

4. **20 min:** [SIGPAC_IMPLEMENTATION_SCRIPTS.md](SIGPAC_IMPLEMENTATION_SCRIPTS.md)
   - Setup inicial
   - Actualización periódica
   - Testing manual

5. **10 min:** Implementar y probar

**Tareas:**
- [ ] Leer EXECUTIVE_SUMMARY
- [ ] Revisar AUDIT (auditoría de componentes)
- [ ] Implementar FIX #2 (crítico)
- [ ] Implementar FIX #1, #3, #4
- [ ] Ejecutar `scripts/test_sigpac_fixes.sh`
- [ ] Probar API

---

### 🛠️ DevOps/SRE

**Ruta de lectura recomendada (1 hora):**

1. **10 min:** [SIGPAC_EXECUTIVE_SUMMARY.md](SIGPAC_EXECUTIVE_SUMMARY.md)
   - Resumen del problema
   - Arquitectura recomendada

2. **15 min:** [SIGPAC_AUDIT_AND_RECOMMENDATIONS.md](SIGPAC_AUDIT_AND_RECOMMENDATIONS.md) — Secciones:
   - 4: Problemas conocidos y mitigaciones
   - 5: Alternativas de descarga masiva
   - 6.1: Arquitectura propuesta

3. **25 min:** [SIGPAC_IMPLEMENTATION_SCRIPTS.md](SIGPAC_IMPLEMENTATION_SCRIPTS.md)
   - Script 1: setup inicial
   - Script 2: actualización nightly (cron)
   - Script 3: validación
   - Script 4: backup/restore

4. **10 min:** Configurar en producción

**Tareas:**
- [ ] Leer EXECUTIVE_SUMMARY
- [ ] Revisar AUDIT (problemas conocidos + mitigaciones)
- [ ] Estudiar IMPLEMENTATION_SCRIPTS
- [ ] Ejecutar `setup_sigpac_initial.sh`
- [ ] Configurar cron con `update_sigpac_nightly.sh`
- [ ] Probar backup/restore

---

### 📊 Project Manager/Product

**Ruta de lectura recomendada (20 min):**

1. **5 min:** [SIGPAC_EXECUTIVE_SUMMARY.md](SIGPAC_EXECUTIVE_SUMMARY.md)
   - Resumen de una página
   - Checklist de implementación
   - Costo de esfuerzo

2. **15 min:** [SIGPAC_AUDIT_AND_RECOMMENDATIONS.md](SIGPAC_AUDIT_AND_RECOMMENDATIONS.md) — Secciones:
   - 1: Auditoría de código (hallazgos)
   - 8: Resumen ejecutivo

**Tareas:**
- [ ] Entender estado actual (hallazgos)
- [ ] Revisar prioridades de fixes
- [ ] Asignar esfuerzo (2-4 horas)
- [ ] Planificar sprint

---

## 🔍 Búsqueda Rápida por Tema

### Mis scripts no funciona — ¿por qué?

→ **[SIGPAC_AUDIT_AND_RECOMMENDATIONS.md](SIGPAC_AUDIT_AND_RECOMMENDATIONS.md) - Sección 1**
- Auditoría línea a línea de `fetch_sigpac.py`, `fetch_sigpac_atom.py`, etc.
- Hallazgos técnicos específicos
- Problemas identificados

### ¿Qué endpoints WFS son correctos en 2024-2025?

→ **[SIGPAC_AUDIT_AND_RECOMMENDATIONS.md](SIGPAC_AUDIT_AND_RECOMMENDATIONS.md) - Sección 2**
- FEGA GeoServer: `https://www.fega.gob.es/geoserver/ows`
- Catastro INSPIRE: `https://www.catastro.minhap.es/webinspire/wfs/CadastralParcel`
- Parámetros WFS correctos (v2.0.0 y v1.1.0)
- Request ejemplos

### ¿Cómo implementar los fixes?

→ **[SIGPAC_CODE_FIXES.md](SIGPAC_CODE_FIXES.md)**
- FIX #1: `backend/config.py` (variables SIGPAC)
- FIX #2: `backend/api/sigpac.py` (parámetros WFS)
- FIX #3: `backend/services/sigpac.py` (usar config)
- FIX #4: `frontend/sigpacService.js` (timeout)
- Código copy-paste listo

### ¿Cuál es la mejor arquitectura?

→ **[SIGPAC_AUDIT_AND_RECOMMENDATIONS.md](SIGPAC_AUDIT_AND_RECOMMENDATIONS.md) - Sección 6**
o **[SIGPAC_EXECUTIVE_SUMMARY.md](SIGPAC_EXECUTIVE_SUMMARY.md) - Sección "¿Qué arquitectura recomiendas?"**

**Resumen:**
- FEGA ATOM (descarga masiva) → PostGIS local (primaria)
- Catastro WFS (fallback tiempo real)
- Redis caché (24h TTL)

### ¿Cómo configurar actualizaciones automáticas?

→ **[SIGPAC_IMPLEMENTATION_SCRIPTS.md](SIGPAC_IMPLEMENTATION_SCRIPTS.md) - Script 2**
- `update_sigpac_nightly.sh` (cron-friendly)
- Detecta cambios ATOM automáticamente
- Backup + limpieza

### ¿Cómo validar que los datos están bien?

→ **[SIGPAC_IMPLEMENTATION_SCRIPTS.md](SIGPAC_IMPLEMENTATION_SCRIPTS.md) - Script 3**
- `validate_sigpac_postgis.py`
- Verifica:
  - Tabla existe
  - Geometrías válidas
  - Índices presentes
  - Campos completos

### ¿Qué hacer si algo falla?

→ **[SIGPAC_IMPLEMENTATION_SCRIPTS.md](SIGPAC_IMPLEMENTATION_SCRIPTS.md) - Script 4**
- `backup_restore_sigpac.sh`
- Backup automático
- Restore manual con confirmación

---

## ✅ Checklist de Implementación General

### FASE 1: Fixes Críticos (30 min)
- [ ] Leer SIGPAC_AUDIT_AND_RECOMMENDATIONS.md (sección 1.4)
- [ ] Aplicar FIX #2 de SIGPAC_CODE_FIXES.md
- [ ] Verificar: `grep "srsName.*EPSG:4326" backend/api/sigpac.py`
- [ ] Probar: `curl http://localhost:8000/api/v1/sigpac/parcels`

### FASE 2: Configuración (1 hora)
- [ ] Aplicar FIX #1 (`backend/config.py`)
- [ ] Aplicar FIX #3 (`backend/services/sigpac.py`)
- [ ] Aplicar FIX #4 (`frontend/src/data/sigpacService.js`)
- [ ] Ejecutar: `bash scripts/test_sigpac_fixes.sh`
- [ ] Tests: `python3 scripts/validate_sigpac_wfs.py`

### FASE 3: Implementar Arquitectura (4 horas)
- [ ] Ejecutar: `bash scripts/setup_sigpac_initial.sh`
- [ ] Validar: `python3 scripts/validate_sigpac_postgis.py`
- [ ] Probar: `curl "http://localhost:8000/api/v1/sigpac/parcels?bbox=-9.3,42.7,-7.4,43.8"`
- [ ] Configurar cron: `update_sigpac_nightly.sh`
- [ ] Probar backup: `bash scripts/backup_restore_sigpac.sh backup`

### FASE 4: Documentación & Testing (1 hora)
- [ ] Actualizar README.md con instrucciones SIGPAC
- [ ] Documentar cómo actualizar datos manualmente
- [ ] Testing de carga en producción
- [ ] Monitoreo: Verificar logs

---

## 🔗 Referencias Externas

### Especificaciones OGC
- [OGC WFS 2.0.0 Spec](https://www.ogc.org/standards/wfs)
- [INSPIRE WFS Guidelines](https://www.inspire-geoportal.eu/)

### Documentación FEGA
- [FEGA - Sistema de Identificación de Parcelas Agrícolas](https://www.fega.gob.es/)
- [FEGA ATOM Feed](https://www.fega.gob.es/orig/atomfeed.xml)

### Documentación Catastro
- [Sede Electrónica del Catastro](https://www.catastro.minhap.es/)
- [Catastro INSPIRE WFS](https://www.catastro.minhap.es/webinspire/wfs/CadastralParcel)

### Herramientas
- [GDAL/ogr2ogr](https://gdal.org/drivers/vector/postgresql.html)
- [PostGIS Documentation](https://postgis.net/)
- [Redis Documentation](https://redis.io/docs/)

---

## 📞 FAQ & Troubleshooting

### P: ¿Puedo usar WFS en tiempo real en lugar de ATOM?
**R:** Sí, pero NO es recomendado como fuente primaria. Úsalo como fallback con caché Redis (24h TTL). ATOM es más confiable para carga masiva.

### P: ¿Cuánto tarda descargar todo SIGPAC de Galicia?
**R:** ~1-2 horas con 2 descargas concurrentes (para no saturar servidor FEGA). Después cargarlo a PostGIS tarda ~30 minutos.

### P: ¿Puedo descargar solo una provincia?
**R:** Sí. Modificar `--provincias 36` en los scripts (36=Pontevedra, 15=Coruña, 27=Lugo, 32=Ourense).

### P: ¿Los datos son legales para usar en producción?
**R:** **SÍ**. FEGA es fuente oficial del gobierno español. Catastro también es oficial. No hay restricciones de uso para datos agrícolas públicos.

### P: ¿Cómo diferencio SIGPAC de Catastro?
**R:** 
- **SIGPAC:** Recintos agrícolas (multiparcelas), código agrícola
- **Catastro:** Parcelas catastrales (más detalladas), referencia catastral
- **Usa:** SIGPAC para agronomía, Catastro para validación

### P: ¿Qué hacer si datos se corrompen?
**R:** Restaurar desde backup con `bash scripts/backup_restore_sigpac.sh restore <backup.dump>`

### P: ¿Cómo acelerar queries?
**R:** Los índices ya están optimizados. Si necesitas más velocidad, usa PostGIS + Redis caché (ya implementado).

---

## 🚀 Quick Start (Para los Impacientes)

```bash
# 1. Implementar FIX crítico (5 min)
cd /home/avarela/XD/practica_2
cp SIGPAC_CODE_FIXES.md /tmp/fixes.md
# → Aplicar FIX #2 manualmente

# 2. Descargar y cargar datos (90 min, mostly waiting)
bash scripts/setup_sigpac_initial.sh

# 3. Validar (5 min)
python3 scripts/validate_sigpac_postgis.py

# 4. Probar API (2 min)
curl "http://localhost:8000/api/v1/sigpac/parcels?bbox=-9.3,42.7,-7.4,43.8"

# 5. Configurar cron (2 min)
crontab -e
# Agregar: 0 3 * * 0 cd /path/to/terragalicia && bash scripts/update_sigpac_nightly.sh
```

**Total:** ~100 minutos (la mayoría es descarga/carga automática)

---

## 📈 Métricas Esperadas

Después de implementar la arquitectura recomendada:

| Métrica | Antes | Después |
|---------|-------|---------|
| Fiabilidad WFS | 95% (con timeouts) | 99.9% (local PostGIS) |
| Latencia bbox query | 1-5s (WFS remote) | <50ms (PostGIS local) |
| Cobertura de datos | Parcial (según cache) | 100% (PostGIS) |
| Costo mensual | $0 | $0 |
| RTO (Recovery Time) | 1h+ | 15 min (restore backup) |

---

## 👨‍💼 Contact & Support

Documentación completamente autosuficiente. Todos los ejemplos de código están listos para copy-paste.

**Si tienes preguntas:**
1. Busca en el índice arriba (CTRL+F)
2. Revisa la sección "FAQ & Troubleshooting"
3. Consulta los documentos específicos referenciados

---

**Estado Final:** 🟢 LISTO PARA IMPLEMENTACIÓN

Todos los archivos están en `/home/avarela/XD/practica_2/`:
```bash
ls -lah SIGPAC_*.md
```

**¡Empezar con SIGPAC_EXECUTIVE_SUMMARY.md!**

## **Fuente de datos: Recintos_Corunha**
- **Ubicación:** `Recintos_Corunha/` (directorio en el repositorio)
- **Número de ficheros:** 94 GeoPackage (`*.gpkg`)
- **Total features:** 3,830,635 (suma de los `recinto` en todos los archivos)
- **Capa:** `recinto` (presente en todos los gpkg)
- **SRS original:** EPSG:4258 (ETRS89, coordenadas geográficas)
- **Geometría:** columna `dn_geom` — POLYGON (se recomienda convertir a MULTIPOLYGON en PostGIS)
- **Atributos por registro:** `dn_oid, provincia, municipio, agregado, zona, poligono, parcela, recinto, dn_surface, pendiente_media, altitud, csp, coef_regadio, uso_sigpac, incidencias, region` (presente en todos los archivos)
- **Notas importantes:**
   - Todos los gpkg comparten esquema homogéneo y SRS; ingesta por lotes es segura.
   - Requiere `ogr2ogr` (GDAL) para carga eficiente y reproyección.
   - Hay un script de carga añadido: `scripts/load_recintos_corunha_to_postgis.sh` (idempotente, detecta SRS, transforma a EPSG:4326, promueve a MULTIPOLYGON, registra conteos y ejecuta deduplicación por `dn_oid`).

**Recomendación rápida para compartir con una LLM**
- Para contexto técnico y operativo (qué hacer, por qué y cómo): comparte `SIGPAC_DEVELOPER_GUIDE.md` y `SIGPAC_IMPLEMENTATION_SCRIPTS.md`.
- Para auditoría y decisiones (hallazgos, riesgos): añade `SIGPAC_AUDIT_AND_RECOMMENDATIONS.md`.
- Para una vista compacta y accionable de referencia al momento de ejecutar tareas: añade `SIGPAC_QUICK_REFERENCE.md`.

Si quieres, puedo extraer muestras (primeras 5 features) de varios gpkg y añadirlas como ejemplos JSON en `data/` para que la LLM tenga ejemplos concretos de atributos y valores.

