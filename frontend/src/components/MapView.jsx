import React, { useEffect } from 'react';
import {
  MapContainer,
  GeoJSON,
  useMap,
} from 'react-leaflet';
import L from 'leaflet';
import { fetchSigpacParcels, computeBoundsFromGeoJson } from '../data/sigpacService.js';
import ParcelPopup from './ParcelPopup.jsx';
import seedParcels from '../../../data/seed/seed_parcels.json';

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
    const sigpacWms = L.tileLayer.wms('https://wms.mapama.gob.es/wms/wms.aspx', {
      layers: 'SIGPAC',
      format: 'image/png',
      transparent: true,
      version: '1.1.1',
      attribution: '&copy; MAPAMA',
      crs: L.CRS.EPSG3857,
    });

    // PNOA Orthophoto (IGN) as WMS
    const pnoaWms = L.tileLayer.wms('https://www.ign.es/wms/pnoa-ma', {
      layers: 'PNOA',
      format: 'image/jpeg',
      transparent: false,
      version: '1.1.1',
      attribution: '&copy; IGN PNOA',
      crs: L.CRS.EPSG3857,
    });

    // OpenStreetMap (reference)
    const osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
    });

    // Always keep OSM as default so map never renders blank when external WMS fails.
    osmLayer.addTo(map);

    // Keep SIGPAC as optional overlay because its endpoint can fail in-browser.
    const baseLayers = {
      'Streets (OpenStreetMap)': osmLayer,
      'Orthophoto (PNOA)': pnoaWms,
    };
    const overlays = {
      'SIGPAC WMS Overlay': sigpacWms,
    };

    const layerControl = L.control.layers(baseLayers, overlays, { collapsed: true }).addTo(map);

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
  const entries = [
    ['PREPARED', 'Prepared'],
    ['FALLOW', 'Fallow'],
    ['PLANTED', 'Planted'],
    ['HARVESTED', 'Harvested'],
  ];

  return (
    <div className="map-legend">
      <h2>Status Legend</h2>
      <ul>
        {entries.map(([status, label]) => (
          <li key={status}>
            <span className={`legend-swatch status-${status.toLowerCase()}`} />
            <span>{label}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function MapView() {
  const [parcelsGeoJson, setParcelsGeoJson] = React.useState(null);
  const [parcelsBounds, setParcelsBounds] = React.useState(null);
  const [parcelSource, setParcelSource] = React.useState('loading');

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
          return;
        }

        console.warn('[PARCELS] Backend SIGPAC returned no features; falling back to local seed parcels');
        setParcelsGeoJson(fallbackGeo);
        setParcelsBounds(fallbackBounds);
        setParcelSource('seed-fallback');
      } catch (e) {
        console.warn('[PARCELS] Backend SIGPAC failed; falling back to local seed parcels:', e?.message || e);
        if (!mounted) return;
        setParcelsGeoJson(fallbackGeo);
        setParcelsBounds(fallbackBounds);
        setParcelSource('seed-fallback');
      }
    })();
    return () => { mounted = false; };
  }, []);

  const onEachFeature = (feature, layer) => {
    layer.on({
      click: () => {
        layer.bindPopup(
          ParcelPopup({ parcel: feature.properties }),
          {
            closeButton: true,
            maxWidth: 320,
            className: 'parcel-popup',
          },
        ).openPopup();
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
      <MapContainer center={mapCenter} zoom={11.5} className="leaflet-map" scrollWheelZoom>
        <WMSLayers />
        <FitToParcels bounds={parcelsBounds} />
        {parcelsGeoJson && (
          <GeoJSON data={parcelsGeoJson} style={parcelStyle} onEachFeature={onEachFeature} />
        )}
      </MapContainer>
      {parcelSource === 'seed-fallback' && (
        <div className="map-data-badge">Parcels source: Local seed fallback</div>
      )}
      {parcelSource === 'backend-sigpac' && (
        <div className="map-data-badge">Parcels source: Backend SIGPAC API</div>
      )}
      <Legend />
    </div>
  );
}
