import React, { useEffect, useState } from 'react';
import {
  MapContainer,
  GeoJSON,
  ZoomControl,
  useMap,
} from 'react-leaflet';
import L from 'leaflet';
import { fetchSigpacParcels, computeBoundsFromGeoJson, BACKEND_BASE_URL } from '../data/sigpacService.js';
import ParcelPopup from './ParcelPopup.jsx';
import WeatherPanel from './WeatherPanel.jsx';
import AgroCopilot from './AgroCopilot.jsx';
import WhatIfSimulator from './WhatIfSimulator.jsx';
import { STATUS_NAMES } from '../data/uiLabels.js';
import seedParcels from '../data/seed_parcels.json';

const mapCenter = [43.331, -8.284];

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

function SigpacOverlayLayer({ enabled, onToast }) {
  const map = useMap();
  const [overlayGeoJson, setOverlayGeoJson] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!enabled) {
      setOverlayGeoJson(null);
      return undefined;
    }

    let cancelled = false;

    const loadOverlay = async () => {
      const bounds = map.getBounds();
      const bbox = [bounds.getWest(), bounds.getSouth(), bounds.getEast(), bounds.getNorth()].join(',');
      setLoading(true);
      try {
        const geo = await fetchSigpacParcels({ bbox });
        if (!cancelled) {
          setOverlayGeoJson(geo);
        }
      } catch (error) {
        if (!cancelled) {
          setOverlayGeoJson(null);
          onToast('Non se puido cargar a capa SIGPAC');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    loadOverlay();
    const handleMoveEnd = () => {
      loadOverlay();
    };
    map.on('moveend', handleMoveEnd);

    return () => {
      cancelled = true;
      map.off('moveend', handleMoveEnd);
    };
  }, [enabled, map, onToast]);

  useEffect(() => {
    if (!enabled) {
      setLoading(false);
    }
  }, [enabled]);

  if (!enabled || !overlayGeoJson) return null;

  return (
    <GeoJSON
      data={overlayGeoJson}
      style={{
        color: '#FF6B35',
        weight: 1,
        fillOpacity: 0.1,
        fillColor: '#FF6B35',
      }}
    />
  );
}

function MapCenterUpdater({ onCenterChange }) {
  const map = useMap();

  useEffect(() => {
    if (!map) return;
    const handleMove = () => {
      const center = map.getCenter();
      onCenterChange([center.lat, center.lng]);
    };
    map.on('moveend', handleMove);
    return () => {
      map.off('moveend', handleMove);
    };
  }, [map, onCenterChange]);

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

export default function MapView() {
  const [parcelsGeoJson, setParcelsGeoJson] = React.useState(null);
  const [parcelsBounds, setParcelsBounds] = React.useState(null);
  const [parcelSource, setParcelSource] = React.useState('loading');
  const [selectedParcel, setSelectedParcel] = React.useState(null);
  const [mapCenter, setMapCenter] = React.useState([43.331, -8.284]);
  const [showSimulator, setShowSimulator] = React.useState(false);
  const [showSigpacOverlay, setShowSigpacOverlay] = React.useState(false);
  const [showWeather, setShowWeather] = React.useState(false);
  const [toastMessage, setToastMessage] = React.useState('');
  const [authToken, setAuthToken] = React.useState(null);
  const authTokenRef = React.useRef(null);

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
  function parcelStyle(feature) {
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

  React.useEffect(() => {
    let mounted = true;
    const fallbackGeo = toFallbackGeoJson(seedParcels);
    const fallbackBounds = computeBoundsFromGeoJson(fallbackGeo);

    // Paint seed parcels immediately so map is never empty
    setParcelsGeoJson(fallbackGeo);
    setParcelsBounds(fallbackBounds);
    setParcelSource('seed-fallback');

    (async () => {
      try {
        const geo = await fetchSigpacParcels();
        if (!mounted) return;
        const count = geo?.features?.length || 0;

        if (count > 0) {
          setParcelsGeoJson(geo);
          setParcelsBounds(computeBoundsFromGeoJson(geo) || fallbackBounds);
          setParcelSource('backend-sigpac');
          console.info(`[PARCELS] Using backend SIGPAC parcels (${count} features)`);
        }
      } catch (e) {
        console.warn('[PARCELS] Backend SIGPAC failed; keeping seed parcels:', e?.message || e);
      }
    })();

    return () => { mounted = false; };
  }, []);

  const onEachFeature = (feature, layer) => {
    layer.on({
      click: async () => {
        const parcelId = feature.properties?.id;
        const refreshPopupInteractions = () => {
          const popupEl = document.querySelector('.leaflet-popup .parcel-popup');
          if (!popupEl || popupEl.dataset.popupWired === '1') return;
          popupEl.dataset.popupWired = '1';

          popupEl.addEventListener('click', async (event) => {
            const areaButton = event.target.closest('[data-area-toggle="true"]');
            if (areaButton) {
              const areaHectares = Number(areaButton.dataset.areaHectares || '0');
              const areaValueEl = popupEl.querySelector('.popup-area-value');
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
          });

          popupEl.addEventListener('change', async (event) => {
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
              layer.setPopupContent(ParcelPopup({ parcel: feature.properties, suitability: null, loading: false }));
            } catch (error) {
              onToast('Erro ao cargar os datos. Téntao de novo.');
            }
          });
        };

          // Show popup immediately with loading state
          layer.bindPopup(
            ParcelPopup({ parcel: feature.properties, suitability: null, loading: true }),
            { closeButton: true, maxWidth: 360, className: 'parcel-popup' }
          ).openPopup();
          // Track selected parcel and wire popup controls
          setSelectedParcel(feature.properties);
          setShowSimulator(false);
          setTimeout(refreshPopupInteractions, 50);

        // Fetch suitability if we have a token and parcel id
        if (authTokenRef.current && parcelId) {
          try {
            const res = await fetch(`${BACKEND_BASE_URL}/parcels/${encodeURIComponent(parcelId)}/suitability`, {
              headers: { 'Authorization': `Bearer ${authTokenRef.current}` },
            });
            if (res.ok) {
              const suitability = await res.json();
              // Update popup with suitability data if still open
              if (layer.isPopupOpen()) {
                layer.setPopupContent(
                  ParcelPopup({ parcel: feature.properties, suitability, loading: false })
                );
              }
            }
          } catch (e) {
            console.warn('[SUITABILITY] Failed to fetch:', e?.message);
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
      <MapContainer center={mapCenter} zoom={11.5} maxZoom={20} className="leaflet-map" scrollWheelZoom zoomControl={false}>
        <ZoomControl position="topright" />
        <button
          type="button"
          className={`sigpac-overlay-button ${showSigpacOverlay ? 'is-active' : ''}`}
          onClick={() => setShowSigpacOverlay((current) => !current)}
        >
          {showSigpacOverlay ? 'Ocultar SIGPAC' : 'Amosar SIGPAC'}
        </button>
        <WMSLayers />
        <SigpacOverlayLayer enabled={showSigpacOverlay} onToast={onToast} />
        <MapCenterUpdater onCenterChange={setMapCenter} />

        <FitToParcels bounds={parcelsBounds} />
        {parcelsGeoJson && (
          <GeoJSON data={parcelsGeoJson} style={parcelStyle} onEachFeature={onEachFeature} />
        )}
        <Legend />
      </MapContainer>
      {parcelSource === 'seed-fallback' && (
        <div className="map-data-badge">Fonte das parcelas: Datos de proba</div>
      )}
      {parcelSource === 'backend-sigpac' && (
        <div className="map-data-badge">Fonte das parcelas: API SIGPAC do backend</div>
      )}
    </div>
  );
}
