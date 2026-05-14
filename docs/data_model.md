# TerraGalicia DSS — Modelo de datos

**Última actualización**: mayo 2026

---

## 1. Tabla principal: `recintos_sigpac`

La tabla central de la aplicación. Contiene los ~3,87 millones de recintos catastrales de la provincia de A Coruña cargados desde los ficheros `.gpkg` oficiales del SIGPAC.

### Esquema real (verificado en PostGIS)

| Columna | Tipo | Nullable | Descripción |
|---|---|---|---|
| `id` | `integer` | NOT NULL | Clave primaria (serial) |
| `provincia` | `integer` | NOT NULL | Código de provincia (15 = A Coruña) |
| `municipio` | `smallint` | NOT NULL | Código de municipio (INE) |
| `agregado` | `smallint` | NOT NULL | Código de agregado catastral |
| `zona` | `integer` | NOT NULL | Zona catastral |
| `poligono` | `smallint` | NOT NULL | Número de polígono |
| `parcela` | `integer` | NOT NULL | Número de parcela |
| `recinto` | `integer` | NOT NULL | Número de recinto dentro de la parcela |
| `dn_surface` | `double precision` | NOT NULL | Superficie declarada en hectáreas |
| `pendiente_media` | `smallint` | NULL | **Pendiente media en décimas de porcentaje** (p.ej. 150 = 15,0 %) |
| `altitud` | `smallint` | NULL | Altitud media del recinto en metros |
| `csp` | `smallint` | NULL | Código de la clase de suelo productivo |
| `coef_regadio` | `smallint` | NULL | Coeficiente de regadío (>0 indica disponibilidad de riego) |
| `uso_sigpac` | `varchar(2)` | NOT NULL | Código de uso del suelo (ver tabla de usos) |
| `incidencias` | `varchar(50)` | NULL | Incidencias catastrales |
| `region` | `integer` | NULL | Región agroclimática |
| `geom` | `geometry(MultiPolygon, 4326)` | NULL | Geometría en WGS 84 |

**Índices**: clave primaria en `id`; dos índices GiST sobre `geom` para consultas espaciales.

> **Nota sobre `pendiente_media`**: el campo se almacena en **décimas de porcentaje**. El backend lo divide entre 10 antes de aplicar las reglas de scoring (`pendiente_pct = pendiente_tenths / 10.0`).

### Códigos de uso SIGPAC más frecuentes

| Código | Descripción |
|---|---|
| `TI` | Tierra de labor en secano |
| `PR` | Prado natural |
| `PA` | Pastizal |
| `FO` | Forestal |
| `VI` | Viñedo |
| `CF` | Cítricos y frutales |
| `ZU` | Zona urbana (excluida del scoring) |
| `ED` | Edificaciones (excluida) |
| `IM` | Improductivo (excluida) |
| `AG` | Corrientes y superficies de agua (excluida) |
| `CA` | Vías de comunicación (excluida) |

---

## 2. Motor de aptitud de cultivos

El endpoint `/api/v1/parcels/{id}/suitability` calcula un ranking de 10 cultivos para cada parcela usando reglas agronómicas explícitas, sin modelos ML. La razón es práctica: no existe un dataset público de rendimientos reales por parcela SIGPAC para A Coruña con la granularidad necesaria para entrenar un modelo.

### Pesos del scoring

| Factor | Variable SIGPAC | Peso |
|---|---|---|
| Pendiente | `pendiente_media` (÷10 → %) | 40 % |
| Disponibilidad de riego | `coef_regadio` | 25 % |
| Mes de siembra actual | fecha del sistema | 20 % |
| Altitud | `altitud` | 15 % |

### Reglas por cultivo

| Cultivo | Pendiente máx. (%) | Riego | Ventana de siembra (meses) | Altitud máx. (m) |
|---|---|---|---|---|
| Millo | 15 | recomendable | abril–mayo (4–5) | 600 |
| Pataca | 20 | opcional | marzo–mayo (3–5) | 900 |
| Trigo | 25 | no necesario | oct.–nov. (10–11) | 800 |
| Centeo | 35 | no necesario | oct.–nov. (10–11) | 1.000 |
| Prado | 45 | no necesario | perenne (sin ventana) | 1.100 |
| Viñedo | 30 | no necesario | perenne (sin ventana) | 700 |
| Castaño | 50 | no necesario | perenne (sin ventana) | 1.000 |
| Horta | 10 | necesario | marzo–junio (3–6) | 600 |
| Frutales | 20 | recomendable | ene.–marzo (1–3) | 700 |
| Pemento | 12 | necesario | marzo–mayo (3–5) | 500 |

### Cálculo del score

Para cada factor se obtiene una puntuación parcial entre 0,0 y 1,0:

- **Pendiente**: 1,0 si `pendiente_pct ≤ pendiente_max`; decaimiento lineal hasta 0,0 en `pendiente_pct = 2 × pendiente_max`.
- **Riego**:
  - `necesario`: 1,0 si `coef_regadio > 0`, si no 0,0.
  - `recomendable`: 1,0 si `coef_regadio > 0`, si no 0,6.
  - `no necesario` / `opcional`: siempre 1,0.
- **Mes**: 1,0 si el mes actual está en la ventana de siembra (o cultivo perenne); 0,0 si está fuera.
- **Altitud**: 1,0 si `altitud ≤ alt_max`; decaimiento lineal hasta 0,0 en `altitud = 2 × alt_max`.

Puntuación final: `score = pend_score × 0,40 + reg_score × 0,25 + mes_score × 0,20 + alt_score × 0,15`

Bandas de color: verde ≥ 70, amarillo 40–69, rojo < 40.

Las parcelas con `uso_sigpac` en `{ZU, ED, IM, AG, CA}` se excluyen directamente del scoring y devuelven `ranking: []`.

El resultado se cachea en Redis con clave `suitability:{parcel_id}` (TTL configurable vía `suitability_cache_ttl_seconds`).

---

## 3. Procedencia de los datos SIGPAC

Los ficheros `.gpkg` de recintos **no se incluyen en el repositorio** (están en `.gitignore`) debido a su tamaño (~2 GB para A Coruña). Hay dos maneras de obtenerlos:

### Opción A — Drive público del proyecto

Los ficheros ya procesados están disponibles en:

> **https://drive.google.com/drive/folders/1xlpSNj61GI-Oe2BClK3AkMArwVim31VZ?usp=sharing**

Descargar todos los ficheros `.gpkg` y colocarlos en la carpeta `Recintos_Corunha/` en la raíz del repositorio. Después seguir los pasos de carga descritos en `README.md`.

### Opción B — Descarga manual vía QGIS

Tutorial de referencia:
> **https://mappinggis.com/2020/03/como-descargar-capas-del-sigpac-en-qgis/**

El proceso consiste en conectar el WFS del SIGPAC desde QGIS (`https://www.mapa.gob.es/es/agricultura/temas/sistema-de-informacion-geografica-de-parcelas-agricolas-sigpac/`), filtrar por provincia (código 15 = A Coruña), exportar cada municipio como `.gpkg` y guardarlos en `Recintos_Corunha/`.

---

## 4. Modelo NGSI-LD (arquitectura objetivo)

TerraGalicia usa FIWARE Orion Context Broker para almacenar entidades agrícolas en formato NGSI-LD. El Orion está activo y el backend escribe entidades en él, aunque el flujo completo (IoT Agent → Orion → QuantumLeap → TimescaleDB) no está operativo todavía.

Las entidades principales del modelo:

| Entidad NGSI-LD | Estado | Descripción |
|---|---|---|
| `AgriFarm` | Activo | Explotación agraria. Atributos: nombre, ubicación, propietario, superficie total. |
| `AgriParcel` | Activo | Parcela individual. Atributos: geometría, área, municipio, estado, cultivo plantado, referencia a `AgriSoil`. |
| `AgriParcelOperation` | Activo | Operación sobre una parcela (siembra, fertilización, cosecha). Atributos: tipo, fecha, producto, cantidad. |
| `AgriCrop` | Definido | Catálogo de cultivos con necesidades agronómicas. |
| `AgriSoil` | Definido | Datos de suelo (pH, textura, materia orgánica, N-P-K). |
| `WeatherObserved` | Definido | Observación meteorológica puntual. |
| `WeatherForecast` | Definido | Previsión meteorológica a 7 días. |
| `AgriParcelRecord` | En stack | Serie temporal de sensores IoT (sin ingestión activa). |
| `AgriFertilizer` | Definido | Inventario de fertilizantes por explotación. |

El `@context` se sirve desde el `context-server` interno (`http://context-server/context.jsonld`) y referencia las definiciones de `smart-data-models/dataModel.Agrifood`.

La historización vía QuantumLeap y la ingestión vía IoT Agent forman parte del trabajo futuro (ver `FUTURE_IMPLEMENTATIONS.md`).
