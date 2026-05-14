import React, { useEffect, useState } from 'react';
import {
  MapContainer,
  ZoomControl,
  useMap,
} from 'react-leaflet';
import L from 'leaflet';
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';
import { fetchSigpacParcels, computeBoundsFromGeoJson, BACKEND_BASE_URL } from '../data/sigpacService.js';
import ParcelPopup from './ParcelPopup.jsx';
import WeatherPanel from './WeatherPanel.jsx';
import AgroCopilot from './AgroCopilot.jsx';
import WhatIfSimulator from './WhatIfSimulator.jsx';
import { STATUS_NAMES } from '../data/uiLabels.js';
import seedParcels from '../data/seed_parcels.json';

// Fix Leaflet marker icon paths broken by Vite's asset pipeline
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
});

const STATUS_COLORS = {
  PLANTED: '#f59e0b',
  FALLOW: '#9ca3af',
  PREPARED: '#22c55e',
  HARVESTED: '#3b82f6',
};

const mapCenter = [43.2792, -8.2100];

function toFallbackGeoJson(seedItems) {
  const features = (seedItems || [])
    .map((item) => {
      const geometry = item?.location?.value;
      if (!geometry || !geometry.type || !geometry.coordinates) return null;
      return {
        type: 'Feature',
        geometry,
        properties: {
          id: item.id,
          name: item?.name?.value || item?.name || null,
          status: item?.parcelStatus?.value || 'UNKNOWN',
          cropName: item?.hasAgriCrop?.object || 'Not assigned',
          soilType: item?.hasAgriSoil?.object || 'Unknown soil',
          area: item?.area?.value ?? null,
          source: 'seed-fallback',
        },
      };
    })
    .filter(Boolean);

  return {
    type: 'FeatureCollection',
    features,
  };
}

// WMS Layer Configuration
function WMSLayers() {
  const map = useMap();

  useEffect(() => {
    // Remove any pre-existing Leaflet layer controls to avoid duplicates
    try {
      const container = map.getContainer();
      if (container) {
        const existing = container.querySelectorAll('.leaflet-control-layers');
        existing.forEach((el) => el.remove());
      }
    } catch (err) {
      // ignore
    }

    // SIGPAC WMS (official) - configured as WMS (not tile fallback)
    // Use WMS version 1.1.1 to keep axis order predictable and request PNG with transparency
    const sigpacWms = L.tileLayer.wms('https://wms.mapa.gob.es/sigpac/wms', {
      layers: 'AU.Sigpac:recinto',
      format: 'image/png',
      transparent: true,
      version: '1.1.1',
      attribution: '&copy; MAPA',
      crs: L.CRS.EPSG3857,
      maxZoom: 19,
    });

    // PNOA Orthophoto (IGN) as WMS
    const pnoaWms = L.tileLayer.wms('https://www.ign.es/wms-inspire/pnoa-ma', {
      layers: 'OI.OrthoimageCoverage',
      format: 'image/jpeg',
      transparent: false,
      version: '1.1.1',
      attribution: '&copy; IGN PNOA',
      crs: L.CRS.EPSG3857,
      maxZoom: 20,
    });

    // OpenStreetMap (reference)
    const osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
    });

    // Always keep OSM as default so map never renders blank when external WMS fails.
    osmLayer.addTo(map);

    const baseLayers = {
      'Rúas (OpenStreetMap)': osmLayer,
      'Ortofoto (PNOA)': pnoaWms,
    };

    const layerControl = L.control.layers(baseLayers, {}, { collapsed: true }).addTo(map);

    // Cleanup on unmount or re-run to prevent duplicate controls
    return () => {
      try {
        if (layerControl) layerControl.remove();
      } catch (e) {
        // ignore
      }
      try {
        if (sigpacWms) sigpacWms.remove();
        if (pnoaWms) pnoaWms.remove();
        if (osmLayer) osmLayer.remove();
      } catch (e) {
        // ignore
      }
    };
  }, [map]);

  return null;
}


function ParcelLayer({ enabled, setParcelsGeoJson, setParcelsBounds, setParcelSource, onFetchingChange, refreshTrigger }) {
  const map = useMap();
  const [loading, setLoading] = React.useState(false);

  useEffect(() => {
    onFetchingChange(loading);
  }, [loading, onFetchingChange]);

  useEffect(() => {
    if (!enabled) {
      setLoading(false);
      setParcelsGeoJson({ type: 'FeatureCollection', features: [] });
      setParcelsBounds(null);
      setParcelSource('empty');
      onFetchingChange(false);
      return undefined;
    }

    let cancelled = false;

    const handleMoveEnd = async () => {
      if (!enabled) return;

      const zoom = map.getZoom();
      if (zoom < 15) {
        setLoading(false);
        onFetchingChange(false);
        setParcelsGeoJson({ type: 'FeatureCollection', features: [] });
        setParcelsBounds(null);
        setParcelSource('empty');
        return;
      }

      const bounds = map.getBounds();
      const bbox = [
        bounds.getWest(),
        bounds.getSouth(),
        bounds.getEast(),
        bounds.getNorth(),
      ].join(',');

      let limit;
      if (zoom >= 17) limit = 2000;
      else if (zoom >= 16) limit = 1000;
      else if (zoom >= 15) limit = 500;
      else limit = 200;

      setLoading(true);
      onFetchingChange(true);

      try {
        const geo = await fetchSigpacParcels({ bbox, zoom, limit });
        if (cancelled) return;

        if (geo && geo.features && geo.features.length > 0) {
          setParcelsGeoJson(geo);
          setParcelsBounds([[bounds.getSouth(), bounds.getWest()], [bounds.getNorth(), bounds.getEast()]]);
          setParcelSource('postgis');
        } else {
          setParcelsGeoJson({ type: 'FeatureCollection', features: [] });
          setParcelsBounds(null);
          setParcelSource('empty');
        }
      } catch (err) {
        console.warn('[PARCELS] moveend fetch error:', err);
      } finally {
        if (!cancelled) {
          setLoading(false);
          onFetchingChange(false);
        }
      }
    };

    handleMoveEnd();
    map.on('moveend', handleMoveEnd);

    return () => {
      cancelled = true;
      map.off('moveend', handleMoveEnd);
      setLoading(false);
      onFetchingChange(false);
    };
  }, [enabled, map, onFetchingChange, setParcelsBounds, setParcelsGeoJson, setParcelSource, refreshTrigger]);

  return null;
}

function MapCenterUpdater({ onCenterChange, onZoomChange }) {
  const map = useMap();

  useEffect(() => {
    if (!map) return;
    const handleMove = () => {
      const center = map.getCenter();
      onCenterChange([center.lat, center.lng]);
      onZoomChange(map.getZoom());
    };
    onZoomChange(map.getZoom());
    map.on('moveend', handleMove);
    return () => {
      map.off('moveend', handleMove);
    };
  }, [map, onCenterChange, onZoomChange]);

  return null;
}

function FitToParcels({ bounds }) {
  const map = useMap();

  useEffect(() => {
    if (!bounds) return;
    const timer = setTimeout(() => {
      map.fitBounds(bounds, {
        padding: [40, 40],
        maxZoom: 13,
      });
    }, 100);
    return () => clearTimeout(timer);
  }, [map, bounds]);

  return null;
}

function Legend() {
  const [collapsed, setCollapsed] = useState(false);
  const [mouseCoords, setMouseCoords] = useState(null);
  const map = useMap();

  useEffect(() => {
    if (!map) return;
    const handleMouseMove = (e) => {
      if (e.latlng) {
        setMouseCoords(e.latlng);
      }
    };
    const handleMouseOut = () => {
      setMouseCoords(null);
    };
    map.on('mousemove', handleMouseMove);
    map.on('mouseout', handleMouseOut);
    return () => {
      map.off('mousemove', handleMouseMove);
      map.off('mouseout', handleMouseOut);
    };
  }, [map]);

  const entries = [
    ['PREPARED', STATUS_NAMES.PREPARED],
    ['FALLOW', STATUS_NAMES.FALLOW],
    ['PLANTED', STATUS_NAMES.PLANTED],
    ['HARVESTED', STATUS_NAMES.HARVESTED],
  ];

  const formatCoords = () => {
    if (!mouseCoords) return '📍 —';
    const lat = Math.abs(mouseCoords.lat);
    const lon = Math.abs(mouseCoords.lng);
    const latDir = mouseCoords.lat >= 0 ? 'N' : 'S';
    const lonDir = mouseCoords.lng >= 0 ? 'E' : 'O';
    return `📍 ${lat.toFixed(4)}° ${latDir}, ${lon.toFixed(4)}° ${lonDir}`;
  };

  return (
    <div className={`map-legend ${collapsed ? 'is-collapsed' : ''}`}>
      {collapsed ? (
        <button
          type="button"
          className="legend-compact-button"
          onClick={() => setCollapsed(false)}
          aria-label="Expandir lenda"
        >
          <span className="legend-compact-badge" aria-hidden="true">🗺</span>
          <span className="legend-compact-title">Lenda</span>
        </button>
      ) : (
        <>
          <div className="legend-header">
            <h2>Lenda</h2>
            <button
              type="button"
              className="legend-collapse-button"
              onClick={() => setCollapsed(true)}
              aria-label="Minimizar lenda"
            >
              ↙
            </button>
          </div>
          <ul>
            {entries.map(([status, label]) => (
              <li key={status}>
                <span className={`legend-swatch status-${status.toLowerCase()}`} />
                <span>{label}</span>
              </li>
            ))}
          </ul>
          <div className="legend-separator" />
          <div className="legend-coords">{formatCoords()}</div>
        </>
      )}
    </div>
  );
}

function MapRefCapture({ mapRef }) {
  const map = useMap();
  mapRef.current = map;
  return null;
}

function ParcelCanvasLayer({ parcelsGeoJson, onEachFeature }) {
  const map = useMap();
  const layerRef = React.useRef(null);
  const rendererRef = React.useRef(null);
  const callbackRef = React.useRef(onEachFeature);

  // Keep callback current without recreating the canvas layer on every render
  React.useEffect(() => { callbackRef.current = onEachFeature; });

  if (!rendererRef.current) {
    rendererRef.current = L.canvas({ padding: 0.5 });
  }

  React.useEffect(() => {
    if (layerRef.current) {
      layerRef.current.remove();
      layerRef.current = null;
    }
    if (!parcelsGeoJson?.features?.length) return undefined;

    const renderer = rendererRef.current;
    layerRef.current = L.geoJSON(parcelsGeoJson, {
      renderer,
      pointToLayer(feature, latlng) {
        const status = feature.properties?.status || 'UNKNOWN';
        const fillColor = STATUS_COLORS[status] || '#64748b';
        return L.circleMarker(latlng, {
          renderer,
          radius: 4,
          fillColor,
          color: '#333',
          weight: 0.5,
          fillOpacity: 0.7,
        });
      },
      style(feature) {
        const status = feature.properties?.status || 'UNKNOWN';
        const fillColor = STATUS_COLORS[status] || '#64748b';
        return {
          color: '#000000',
          weight: 1.5,
          opacity: 0.85,
          fillColor,
          fillOpacity: 0.4,
        };
      },
      onEachFeature(feature, layer) {
        callbackRef.current(feature, layer);
      },
    }).addTo(map);

    return () => {
      if (layerRef.current) {
        layerRef.current.remove();
        layerRef.current = null;
      }
    };
  }, [parcelsGeoJson, map]);

  return null;
}

export default function MapView() {
  const [parcelsGeoJson, setParcelsGeoJson] = React.useState(null);
  const [, setParcelsBounds] = React.useState(null);
  const [parcelSource, setParcelSource] = React.useState('loading');
  const [currentZoom, setCurrentZoom] = React.useState(13);
  const [isParcelFetching, setIsParcelFetching] = React.useState(false);
  const [selectedParcel, setSelectedParcel] = React.useState(null);
  const [mapCenter, setMapCenter] = React.useState([43.2792, -8.2100]);
  const [showSimulator, setShowSimulator] = React.useState(false);
  const [showSigpacOverlay, setShowSigpacOverlay] = React.useState(false);
  const [refreshTrigger, setRefreshTrigger] = React.useState(0);
  const [showWeather, setShowWeather] = React.useState(false);
  const [toastMessage, setToastMessage] = React.useState('');
  const [authToken, setAuthToken] = React.useState(null);
  const authTokenRef = React.useRef(null);
  const mapRef = React.useRef(null);
  const popupRef = React.useRef(null);

  const onToast = React.useCallback((message) => {
    setToastMessage(message);
    window.clearTimeout(window.__tgToastTimer);
    window.__tgToastTimer = window.setTimeout(() => {
      setToastMessage('');
    }, 3000);
  }, []);

  React.useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${BACKEND_BASE_URL}/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: new URLSearchParams({
            username: 'farmer1',
            password: 'farmer123',
            grant_type: 'password',
          }),
        });
        if (res.ok) {
          const data = await res.json();
          authTokenRef.current = data.access_token;
          setAuthToken(data.access_token);
          console.info('[AUTH] Demo token obtained successfully');
        }
      } catch (e) {
        console.warn('[AUTH] Could not obtain demo token:', e?.message);
      }
    })();
  }, []);

  // Parcel style functions (moved from mockParcels)
  function getParcelColor(feature) {
    const status = feature.properties?.status || 'UNKNOWN';
    return (
      {
        PLANTED: '#f59e0b',
        FALLOW: '#9ca3af',
        PREPARED: '#22c55e',
        HARVESTED: '#3b82f6',
      }[status] || '#64748b'
    );
  }

  function parcelStyle(feature) {
    const fillColor = getParcelColor(feature);

    if (feature.properties?.geometry_type === 'centroid') {
      return {
        radius: 3,
        fillColor,
        color: '#333',
        weight: 0.5,
        fillOpacity: 0.7,
      };
    }

    return {
      color: '#000000',
      weight: 2,
      opacity: 0.85,
      fillColor,
      fillOpacity: 0.4,
      lineCap: 'round',
      lineJoin: 'round',
    };
  }

  function parcelHoverStyle(feature) {
    const status = feature.properties?.status || 'UNKNOWN';
    const fillColor =
      {
        PLANTED: '#f59e0b',
        FALLOW: '#9ca3af',
        PREPARED: '#22c55e',
        HARVESTED: '#3b82f6',
      }[status] || '#64748b';

    return {
      color: '#000000',
      weight: 3,
      opacity: 1,
      fillColor,
      fillOpacity: 0.6,
      lineCap: 'round',
      lineJoin: 'round',
    };
  }



  const onEachFeature = (feature, layer) => {
    layer.on({
      click: async (e) => {
        L.DomEvent.stopPropagation(e);
        const parcelId = feature.properties?.id;
        const refreshPopupInteractions = () => {
          // The Leaflet `className` option applies the class to the .leaflet-popup container
          // so we must target the popup container with that class and then its content element.
          const popupContent = document.querySelector('.leaflet-popup.parcel-popup .leaflet-popup-content');
          if (!popupContent || popupContent.dataset.popupWired === '1') return;
          popupContent.dataset.popupWired = '1';

          popupContent.addEventListener('click', async (event) => {
            const areaButton = event.target.closest('[data-area-toggle="true"]');
            if (areaButton) {
              console.log('AREA TOGGLE CLICKED');
              const areaHectares = Number(areaButton.dataset.areaHectares || '0');
              const areaValueEl = popupContent.querySelector('.popup-area-value');
              const currentUnit = areaValueEl?.dataset.areaUnit || 'ha';
              const nextUnit = currentUnit === 'ha' ? 'm2' : 'ha';
              if (areaValueEl) {
                areaValueEl.textContent = nextUnit === 'ha'
                  ? `${new Intl.NumberFormat('gl-ES', { maximumFractionDigits: 2 }).format(areaHectares)} ha`
                  : `${new Intl.NumberFormat('gl-ES', { maximumFractionDigits: 0 }).format(areaHectares * 10000)} m²`;
                areaValueEl.dataset.areaUnit = nextUnit;
              }
              areaButton.textContent = nextUnit === 'ha' ? 'm²' : 'ha';
              areaButton.dataset.areaUnit = nextUnit;
            }

            const simulateButton = event.target.closest('.simulate-btn');
            if (simulateButton) {
              setShowSimulator(true);
            }
            const expandBtn = event.target.closest('.suitability-expand-btn');
            if (expandBtn) {
              const popup = popupContent;
              const full = popup.querySelector('.popup-ranking-full');
              if (!full) return;
              full.style.display = full.style.display === 'none' ? 'block' : 'none';
            }
          });

          popupContent.addEventListener('change', async (event) => {
            const statusSelect = event.target.closest('.status-select');
            if (!statusSelect) return;
            const newStatus = statusSelect.value;
            const parcelIdToUpdate = statusSelect.dataset.parcelId;
            try {
              const res = await fetch(`${BACKEND_BASE_URL}/parcels/${encodeURIComponent(parcelIdToUpdate)}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ parcelStatus: newStatus }),
              });
              if (!res.ok) throw new Error('HTTP ' + res.status);
              feature.properties.status = newStatus;
              popupRef.current?.setContent(ParcelPopup({ parcel: feature.properties, suitability: null, loading: false }));
              setTimeout(refreshPopupInteractions, 50);
            } catch (error) {
              onToast('Erro ao cargar os datos. Téntao de novo.');
            }
          });
        };

          // Open popup attached to the map (not the layer) so it survives layer re-renders
          const _map = mapRef.current;
          if (_map) {
            if (popupRef.current) popupRef.current.remove();
            popupRef.current = L.popup({
              closeButton: true,
              maxWidth: 260,
              maxHeight: 380,
              className: 'parcel-popup',
              autoPanPaddingTopLeft: [10, 100],
              closeOnClick: false,
              autoClose: false,
            })
              .setLatLng(e.latlng)
              .setContent(ParcelPopup({ parcel: feature.properties, suitability: null, loading: true }))
              .openOn(_map);
          }
          setSelectedParcel(feature.properties);
          setShowSimulator(false);
          setTimeout(refreshPopupInteractions, 50);

        // Fetch suitability if we have a token and parcel id
        if (authTokenRef.current && parcelId) {
          try {
            const res = await fetch(`${BACKEND_BASE_URL}/parcels/${encodeURIComponent(parcelId)}/suitability`, {
              headers: { 'Authorization': `Bearer ${authTokenRef.current}` },
            });
            const body = await res.json().catch(() => null);
            if (res.ok) {
              const suitability = body || { ranking: [] };
              // Update popup content in DOM without closing popup
              if (popupRef.current?.isOpen()) {
                const popupContent = document.querySelector('.leaflet-popup.parcel-popup .leaflet-popup-content');
                if (popupContent) {
                  // Find suitability section and update it in-place
                  const suitSection = popupContent.querySelector('.popup-suitability');
                  if (suitSection && suitability?.ranking?.length > 0) {
                    const ranking = suitability.ranking;
                    const top = ranking[0];
                    const topCropId = top.cropId?.split(':').pop?.() || top.cropId || '';
                    const topLabel = top.cropId ? (window.getReadableCropLabel?.(topCropId) || topCropId) : 'N/A';
                    const topScore = top.score <= 1 ? Math.round(top.score * 100) : Math.round(top.score);
                    const topRec = suitSection.querySelector('.popup-top-recommendation');
                    if (topRec) {
                      topRec.innerHTML = `<span class="popup-crop-id">${topLabel}</span><span class="popup-score-pct">${topScore}%</span>`;
                    }
                  }
                }
              }
            } else {
              // Non-ok: show error message in place
              const suitability = body || { error: `HTTP ${res.status}` };
              if (popupRef.current?.isOpen()) {
                const popupContent = document.querySelector('.leaflet-popup.parcel-popup .leaflet-popup-content');
                if (popupContent) {
                  const suitSection = popupContent.querySelector('.popup-suitability');
                  if (suitSection) {
                    suitSection.innerHTML = `<div class="popup-suitability-error">${suitability.error || 'Erro descoñecido'}</div>`;
                  }
                }
              }
            }
          } catch (e) {
            console.warn('[SUITABILITY] Failed to fetch:', e?.message);
            if (popupRef.current?.isOpen()) {
              const popupContent = document.querySelector('.leaflet-popup.parcel-popup .leaflet-popup-content');
              if (popupContent) {
                const suitSection = popupContent.querySelector('.popup-suitability');
                if (suitSection) {
                  suitSection.innerHTML = `<div class="popup-suitability-error">Erro ao cargar a recomendación</div>`;
                }
              }
            }
          }
        }
      },
      mouseover: () => {
        layer.setStyle(parcelHoverStyle(feature));
        layer.bringToFront();
      },
      mouseout: () => {
        layer.setStyle(parcelStyle(feature));
      },
    });
  };

  return (
    <div className="map-shell">
      {toastMessage && <div className="map-toast">{toastMessage}</div>}

      <div className="sigpac-controls">
        <div className="sigpac-controls-row">
          {showSigpacOverlay && currentZoom >= 15 && !isParcelFetching && (parcelsGeoJson?.features?.length || 0) > 0 && (
            <span className="sigpac-source-label">
              {parcelSource === 'postgis' ? 'Fonte: PostGIS' : 'Fonte: GeoPackage'}
            </span>
          )}
          <button
            type="button"
            className={`sigpac-toggle-btn ${showSigpacOverlay ? 'is-active' : ''}`}
            onClick={() => setShowSigpacOverlay((current) => !current)}
          >
            {showSigpacOverlay ? 'Ocultar SIGPAC' : 'Amosar SIGPAC'}
          </button>
          {showSigpacOverlay && (
            <button
              type="button"
              className="sigpac-refresh-btn"
              onClick={() => setRefreshTrigger((n) => n + 1)}
              disabled={isParcelFetching}
            >
              Refrescar
            </button>
          )}
        </div>
        {showSigpacOverlay && parcelsGeoJson?.truncated && (
          <div className="sigpac-truncated-banner">
            Amosando 5000 parcelas. Fai zoom ou usa Refrescar para ver outras.
          </div>
        )}
      </div>

      <div className="floating-action-group">
        <WeatherPanel
          mapCenter={mapCenter}
          open={showWeather}
          onToggle={() => setShowWeather((current) => !current)}
          onClose={() => setShowWeather(false)}
        />
        <AgroCopilot parcelId={selectedParcel?.id} authToken={authToken} />
      </div>
      {showSimulator && selectedParcel && (
        <WhatIfSimulator parcelId={selectedParcel.id} authToken={authToken} onClose={() => setShowSimulator(false)} />
      )}
      <MapContainer center={mapCenter} zoom={13} maxZoom={20} className="leaflet-map" scrollWheelZoom zoomControl={false} closePopupOnClick={false}>
        <ZoomControl position="topright" />
        <WMSLayers />
        <MapRefCapture mapRef={mapRef} />
        <MapCenterUpdater onCenterChange={setMapCenter} onZoomChange={setCurrentZoom} />
        <ParcelLayer
          enabled={showSigpacOverlay}
          setParcelsGeoJson={setParcelsGeoJson}
          setParcelsBounds={setParcelsBounds}
          setParcelSource={setParcelSource}
          onFetchingChange={setIsParcelFetching}
          refreshTrigger={refreshTrigger}
        />
        <ParcelCanvasLayer
          parcelsGeoJson={parcelsGeoJson}
          onEachFeature={onEachFeature}
        />
        <Legend />
      </MapContainer>
      {/* Badge hidden when source label is already shown inside sigpac-controls-row */}
      {(parcelSource !== 'loading' || showSigpacOverlay) &&
        !(showSigpacOverlay && currentZoom >= 15 && !isParcelFetching && (parcelsGeoJson?.features?.length || 0) > 0) && (
        <div className="map-data-badge">
          {(!showSigpacOverlay || currentZoom < 15)
            ? 'Preme Amosar SIGPAC e fai zoom para ver parcelas'
            : isParcelFetching
              ? 'Cargando...'
              : 'Preme Amosar SIGPAC e fai zoom para ver parcelas'}
        </div>
      )}
    </div>
  );
}
