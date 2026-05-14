export const BACKEND_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export async function fetchSigpacParcels({ baseUrl = BACKEND_BASE_URL, bbox, zoom = null, limit = null } = {}) {
  const url = new URL(`${baseUrl}/sigpac/parcels`);
  if (bbox) {
    url.searchParams.set('bbox', bbox);
  }
  if (zoom !== null) {
    url.searchParams.set('zoom', zoom);
  }
  if (limit !== null) {
    url.searchParams.set('limit', limit);
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 25000);

  try {
    const response = await fetch(url.toString(), { signal: controller.signal });

    if (!response.ok) {
      throw new Error(`Backend SIGPAC API failed with HTTP ${response.status}`);
    }

    const payload = await response.json();

    if (payload?.type !== 'FeatureCollection' || !Array.isArray(payload?.features)) {
      throw new Error('Backend SIGPAC API returned an invalid GeoJSON FeatureCollection');
    }

    if (payload.features.length === 0) {
      return { type: 'FeatureCollection', features: [], dataSource: 'empty',
               truncated: false, total_estimate: 0, returned: 0 };
    }

    const dataSource = payload.features?.[0]?.properties?.source || 'unknown';

    return {
      type: payload.type,
      features: payload.features,
      dataSource,
      truncated: payload.truncated ?? false,
      total_estimate: payload.total_estimate ?? payload.features.length,
      returned: payload.returned ?? payload.features.length,
    };
  } catch (error) {
    if (controller.signal.aborted) {
      throw new Error('SIGPAC timeout after 25s');
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

export function computeBoundsFromGeoJson(geojson) {
  const coords = [];
  if (!geojson || !geojson.features) return null;
  geojson.features.forEach((f) => {
    const geom = f.geometry;
    if (!geom) return;
    if (geom.type === 'Polygon') {
      geom.coordinates.forEach((ring) => ring.forEach((pt) => coords.push(pt)));
    } else if (geom.type === 'MultiPolygon') {
      geom.coordinates.forEach((poly) => poly.forEach((ring) => ring.forEach((pt) => coords.push(pt))));
    }
  });
  if (!coords.length) return null;
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  coords.forEach(([x, y]) => {
    if (x < minX) minX = x;
    if (x > maxX) maxX = x;
    if (y < minY) minY = y;
    if (y > maxY) maxY = y;
  });
  return [ [minY, minX], [maxY, maxX] ];
}
