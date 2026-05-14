# Implementaciones futuras

## Contratiempo durante el desarrollo

El principal problema que encontramos fue la obtención de los datos reales del SIGPAC. Durante aproximadamente dos semanas no conseguimos hacer funcionar la descarga directa de los ficheros `.gpkg` de forma automatizada, lo que bloqueó toda la parte de visualización real de parcelas. Al final lo resolvimos por dos vías: descargando los datos manualmente desde QGIS siguiendo el proceso estándar de descarga por provincia, y publicando los ficheros ya procesados en un Drive público del proyecto para que cualquier evaluador pueda cargarlos directamente. Una vez que teníamos los ~3,8 millones de recintos de A Coruña cargados en PostGIS, el resto del pipeline (backend, canvas renderer, popup con datos reales, scoring) funcionó sin grandes sorpresas. La pérdida de tiempo fue real y redujo el margen que teníamos para algunas funcionalidades que habíamos planificado.

---

## Funcionalidades que nos habría gustado incluir en esta entrega

### Animación del tiempo actual

La idea era mostrar un visor animado de radar de precipitación directamente sobre el mapa, con frames temporales en loop para dar contexto de lo que está pasando en tiempo real sobre las parcelas. Queríamos usar alguna fuente de tiles meteorológicos animados (RainViewer u Open-Meteo tienen algo similar). Quedó fuera porque después de recuperar el retraso de los datos SIGPAC simplemente no quedó margen. El panel de tiempo actual (temperatura, humedad, previsión a 7 días) está implementado, pero sin la capa animada sobre el mapa.

### Toggle de tema claro/oscuro

Un conmutador global de tema para toda la interfaz. El CSS ya tiene definidas variables de color, así que el cambio no sería enorme, pero requiere trabajo tanto en los estilos del mapa Leaflet como en los componentes React. Lo dejamos para después porque era más cosmético que funcional y el tiempo era limitado.

### Persistencia del estado de parcela en base de datos

Actualmente el estado de cada parcela (PLANTADA, BARBECHO, PREPARADA, COSECHADA) se guarda en memoria y se pierde al recargar la página. La estructura para persistirlo en PostgreSQL o en Orion está preparada en el backend, pero no llegamos a conectar el flujo completo. Esto es un problema real de usabilidad que habría que resolver antes de que la herramienta fuera útil en producción.

### LLM real para el AgroCopilot

El chat del AgroCopilot funciona, pero cuando no hay un servicio LLM configurado responde con mensajes de fallback genéricos. Conectar un Ollama local o una API de OpenAI-compatible debería ser relativamente directo dado que el cliente ya está implementado, pero no lo pusimos en marcha porque queríamos asegurarnos de que el resto de la aplicación funcionaba primero.

### Tiles vectoriales (MVT) para el visor SIGPAC

Con el canvas renderer actual se pueden mostrar hasta 5000 parcelas por petición de forma fluida. Para zooms bajos donde hay más de 5000 recintos en el viewport aparece el banner de aviso y el usuario tiene que hacer zoom. La solución correcta sería generar tiles vectoriales (MVT) desde PostGIS o usar pg_tileserv para servir las parcelas a cualquier nivel de zoom sin límite. Es una mejora de rendimiento importante que requiere más tiempo de implementación del que teníamos.

### Integración activa de IoT Agent y QuantumLeap

El stack FIWARE completo arranca con `docker-compose up -d` y todos los servicios están en pie (IoT Agent, QuantumLeap, TimescaleDB, MQTT broker), pero no hay flujos de datos activos pasando por ellos. La intención era conectar las APIs meteorológicas a través del IoT Agent para que los datos de tiempo se historicen en TimescaleDB vía QuantumLeap, siguiendo el patrón de referencia FIWARE. No llegamos a cerrar ese ciclo; el panel de tiempo va directo a Open-Meteo desde el backend.

### Dashboard Grafana embebido

Grafana está en el stack y es accesible en `http://localhost:3001`, pero sin paneles configurados. La idea era tener dashboards con históricos de tiempo por zona, distribución de usos del suelo, y métricas operacionales básicas de la aplicación. Queda como trabajo futuro una vez que TimescaleDB tenga datos reales.

### Alertas de heladas y plagas

Tenemos en el PRD los requisitos de alertas automáticas basadas en la previsión (si la temperatura mínima cae por debajo de 0 °C en 72 horas, alertar a los agricultores). Implementarlo requiere tanto un sistema de notificaciones como los modelos fenológicos para las plagas. Lo dejamos para la Fase 2 porque dependía de tener la integración meteorológica más madura y usuarios reales con parcelas registradas.

### Dashboard cooperativo multi-parcela

La persona de Rosa (gestora de cooperativa) en el PRD requiere una vista consolidada de todas las parcelas de los miembros de la cooperativa. El modelo de datos lo soporta, pero la interfaz de gestión multi-usuario (registro, asignación de parcelas, permisos por rol) no está implementada. Actualmente solo hay un usuario demo.

### Capacidad offline y sincronización

Service worker para que la app funcione sin conexión con los últimos datos descargados. Lo dejamos fuera porque añade complejidad de infraestructura y queríamos tener primero la versión online estable.
