const BACKEND_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export async function fetchSigpacParcels({ baseUrl = BACKEND_BASE_URL } = {}) {
  const url = `${baseUrl}/sigpac/parcels`;
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`Backend SIGPAC API failed with HTTP ${response.status}`);
  }

  const payload = await response.json();
  if (payload?.type !== 'FeatureCollection' || !Array.isArray(payload?.features)) {
    throw new Error('Backend SIGPAC API returned an invalid GeoJSON FeatureCollection');
  }

  return payload;
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
