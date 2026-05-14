# TerraGalicia DSS

**Versión**: 1.2 — Mayo 2026 — Proyecto académico (MVP parcial operativo)

---

## Objetivo

TerraGalicia es un sistema de apoyo a la decisión agrícola (DSS) desarrollado como proyecto académico. La idea de partida es sencilla: Galicia tiene casi 400.000 explotaciones agrarias, muchas de ellas minifundios gestionados por una sola persona, y aunque los datos del SIGPAC son públicos y gratuitos, la interfaz oficial está pensada para técnicos administrativos, no para quien trabaja la tierra. TerraGalicia intenta cerrar esa brecha: ofrece los mismos datos catastrales con una capa de información adicional (aptitud de cultivos, previsión meteorológica, historial de operaciones) sobre un mapa interactivo.

El alcance es académico. No buscamos sustituir plataformas profesionales como DSSAT ni las herramientas de la Xunta de Galicia; lo que queremos demostrar es que con datos públicos, FIWARE como capa de interoperabilidad y un backend Python sobre PostGIS es posible construir algo funcional y útil.

---

## Estado del arte

Los sistemas DSS agrícolas más extendidos (CropX, Trimble Ag, John Deere Operations Center) tienen costes de suscripción que hacen inviable su adopción en el minifundio gallego. Dentro del mundo del software libre, el patrón FIWARE for Agri e iniciativas como Smart Agrifood Solutions muestran que el estándar NGSI-LD encaja bien para modelar entidades agrícolas, aunque la mayoría de los proyectos publicados se quedan en fase de demostración.

Para el componente de scoring de aptitud de cultivos la alternativa natural sería un modelo de machine learning. No lo usamos por una razón concreta: no existe un dataset público de rendimientos por parcela SIGPAC con la granularidad necesaria para A Coruña, y entrenar con datos genéricos producirá un modelo que no mejora las reglas agronómicas básicas de la región. Las reglas que implementamos —pendiente máxima, ventana de siembra, necesidades de riego, altitud máxima— están extraídas de manuales agronómicos gallegos y ponderadas con pesos que reflejan la realidad física del territorio: la pendiente tiene el mayor peso (40%) porque en Galicia es el factor limitante más frecuente.

---

## Funcionalidades operativas

Lo que está funcionando a día de hoy:

- **Visor de parcelas SIGPAC** — carga desde PostGIS (~3,87 M recintos de A Coruña) con renderizado sobre canvas Leaflet. Hasta 5.000 parcelas por petición; banner de aviso si hay más en el viewport.
- **Popup de parcela** — ID catastral, área (toggle ha/m²), municipio, uso SIGPAC, fuente de datos, estado actual con selector.
- **Scoring de aptitud de cultivos** — ranking de 10 cultivos con barras de puntuación y desglose de los cuatro factores (pendiente, riego, mes, altitud). Colores verde/amarillo/rojo según umbral.
- **Panel de tiempo** — condiciones actuales y previsión a 7 días vía Open-Meteo (API libre, sin clave).
- **AgroCopilot** — interfaz de chat. Con `LLM_API_KEY` configurado responde con contexto de la parcela; sin él devuelve mensajes de fallback explicativos.
- **Simulador what-if** — ajusta fecha de siembra, tipo de cultivo y disponibilidad de riego; recalcula probabilidad de éxito en tiempo real.
- **Autenticación JWT** — login automático al cargar la app con el usuario demo (`farmer1` / `farmer123`).
- **API de operaciones** — registro y consulta de operaciones por parcela (`GET/POST /api/v1/parcels/{id}/operations`).
- **FIWARE Orion** — activo; almacena entidades `AgriFarm`, `AgriParcel` y operaciones como NGSI-LD.

---

## Descripción detallada

### Mapa

Al abrir la aplicación el mapa centra en A Coruña (43.28°N, 8.21°O) a zoom 13. Las parcelas SIGPAC solo se cargan a partir del zoom 15; por debajo aparece un aviso. El control de capas (esquina superior derecha) permite alternar entre callejero (OSM) y ortofoto del PNOA (IGN).

El color de cada parcela indica su estado: verde (PREPARADA), naranja (PLANTADA), gris (BARBECHO), azul (COSECHADA). Los estados se guardan actualmente en memoria y se pierden al recargar; la persistencia en base de datos es trabajo futuro.

### Popup de parcela

Al hacer clic en una parcela aparece un popup con los datos del recinto: ID, nombre, área (clic para cambiar entre ha y m²), municipio, uso oficial, tipo de suelo y fuente del dato (PostGIS o GeoPackage local). Debajo, el ranking de aptitud de cultivos se carga de forma asíncrona desde `/api/v1/parcels/{id}/suitability`. El selector de estado permite cambiar el estado del recinto con un PATCH al backend. El botón **Simular** abre el simulador precargado con los datos de esa parcela.

### Panel de tiempo

Botón circular azul en la esquina inferior derecha. Muestra temperatura, humedad, viento y precipitación para las coordenadas del centro del mapa, más la previsión diaria a 7 días. Los datos vienen de Open-Meteo. El botón de refresco vuelve a consultar la API.

### AgroCopilot

Botón circular verde, también en la esquina inferior derecha. Abre un panel de chat lateral. Cada sesión se carga con el contexto de la parcela seleccionada (si hay una). Con un servicio LLM configurado vía `LLM_API_KEY` y `LLM_API_BASE`, el copiloto responde con información específica de la parcela; sin él, los mensajes de fallback describen qué haría y qué datos usaría.

### Simulador what-if

Permite ajustar tres parámetros: fecha de siembra (slider de semanas desde hoy), tipo de cultivo (desplegable con los 10 cultivos del catálogo) y si se asume disponibilidad de riego (toggle). La puntuación se recalcula en tiempo real usando las mismas reglas del motor de aptitud pero parametrizadas con los valores del simulador en lugar de los de la parcela real.

---

## Referencia técnica

El stack completo (14 servicios Docker) y el pipeline de datos SIGPAC están documentados en [docs/architecture.md](architecture.md).

El esquema real de `recintos_sigpac`, las reglas de scoring de los 10 cultivos y las fuentes de datos se describen en [docs/data_model.md](data_model.md).

Las funcionalidades que quedaron fuera del MVP por restricciones de tiempo están en [FUTURE_IMPLEMENTATIONS.md](../FUTURE_IMPLEMENTATIONS.md).
