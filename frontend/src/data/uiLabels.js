export const SOIL_NAMES = {
  'atlantic-acid': 'Solo Ácido Atlántico',
  alluvial: 'Solo Aluvial',
  'coastal-sandy': 'Solo Costeiro Areoso',
  'hillside-clay': 'Solo Arxiloso de Ladeira',
};

export const CROP_NAMES = {
  // Crops from suitability scoring rules
  millo: 'Millo',
  pataca: 'Pataca',
  trigo: 'Trigo',
  centeo: 'Centeo',
  prado: 'Prado',
  viñedo: 'Viñedo',
  castano: 'Castiñeiro',
  horta: 'Horta',
  frutales: 'Froiteiras',
  pemento: 'Pemento de Padrón',
  // Additional crops in catalog
  kiwi: 'Kiwi',
  albarino: 'Uva Albariño',
  mencia: 'Uva Mencía',
  grelos: 'Grelos',
  // Legacy/aliases
  potatoe: 'Pataca',
  maize: 'Millo',
  potato: 'Pataca',
};

export const USO_SIGPAC_NAMES = {
  TI: 'Terra labrable',
  VI: 'Viñedo',
  FY: 'Froiteiras',
  PA: 'Pasto',
  PR: 'Pasto con arborado',
  OV: 'Olivar',
  ZU: 'Solo urbano',
  ED: 'Edificacións',
  IM: 'Improductivo',
  AG: 'Augas',
  CA: 'Canles',
};

export function getReadableUsoSigpac(value) {
  return translateLabel(value, USO_SIGPAC_NAMES) || extractTextValue(value) || '';
}

export const STATUS_NAMES = {
  PLANTED: '🌱 Plantada',
  FALLOW: '💤 Barbecho',
  PREPARED: '🔧 Preparada',
  HARVESTED: '🌾 Colleitada',
};

export const STATUS_SHORT_NAMES = {
  PLANTED: 'Plantada',
  FALLOW: 'Barbecho',
  PREPARED: 'Preparada',
  HARVESTED: 'Colleitada',
};

export const CROP_OPTIONS = ['millo', 'pataca', 'kiwi', 'albarino', 'mencia', 'grelos', 'trigo', 'centeo'];

export const AREA_NUMBER_FORMAT = new Intl.NumberFormat('gl-ES', {
  maximumFractionDigits: 2,
});

export const AREA_M2_FORMAT = new Intl.NumberFormat('gl-ES', {
  maximumFractionDigits: 0,
});

export function extractTextValue(value) {
  if (value == null) return '';
  if (typeof value === 'string' || typeof value === 'number') return String(value);
  if (typeof value === 'object') {
    if ('value' in value) return extractTextValue(value.value);
    if ('object' in value) return extractTextValue(value.object);
  }
  return '';
}

export function lastUrnSegment(value) {
  const raw = extractTextValue(value).trim();
  if (!raw) return '';
  const parts = raw.split(':').filter(Boolean);
  if (!parts.length) return raw;
  let segment = parts[parts.length - 1];
  if (/^\d+$/.test(segment) && parts.length > 1) {
    segment = parts[parts.length - 2];
  }
  return segment;
}

export function cleanLabel(value) {
  const text = extractTextValue(value).trim();
  if (!text) return '';
  const normalized = text.replace(/[-_]+/g, ' ').trim();
  return normalized.charAt(0).toUpperCase() + normalized.slice(1);
}

export function translateLabel(value, map) {
  const key = lastUrnSegment(value);
  if (!key) return '';
  return map[key] || cleanLabel(key);
}

export function getReadableSoilLabel(value) {
  return translateLabel(value, SOIL_NAMES);
}

export function getReadableCropLabel(value) {
  return translateLabel(value, CROP_NAMES);
}

export function getReadableStatusLabel(status) {
  const key = extractTextValue(status).trim().toUpperCase();
  return STATUS_NAMES[key] || cleanLabel(key);
}

export function getPlainStatusLabel(status) {
  const key = extractTextValue(status).trim().toUpperCase();
  return STATUS_SHORT_NAMES[key] || cleanLabel(key);
}

export function getParcelTitle(parcel) {
  const name = extractTextValue(parcel?.name || parcel?.displayName || parcel?.label).trim();
  if (name) return name;

  const id = extractTextValue(parcel?.id || parcel?.gid || parcel?.ref);
  if (!id) return 'Parcela';

  const match = id.match(/AgriParcel:([^:]+):([^:]+)$/);
  if (match) {
    return `Parcela ${match[1]}-${match[2]}`;
  }

  const parts = id.split(':').filter(Boolean);
  if (parts.length >= 2) {
    return `Parcela ${parts[parts.length - 2]}-${parts[parts.length - 1]}`;
  }

  return `Parcela ${cleanLabel(id)}`;
}

export function getCropValue(parcel) {
  return extractTextValue(parcel?.cropName || parcel?.cultivo || parcel?.hasAgriCrop);
}

export function getSoilValue(parcel) {
  return extractTextValue(parcel?.soilType || parcel?.hasAgriSoil);
}

export function getStatusValue(parcel) {
  return extractTextValue(parcel?.status || parcel?.parcelStatus).trim().toUpperCase() || 'UNKNOWN';
}

export function getAreaHectares(parcel) {
  const raw = parcel?.area;
  if (typeof raw === 'number') return raw;
  if (raw && typeof raw === 'object') {
    if (typeof raw.value === 'number') return raw.value;
    if (typeof raw.value === 'string') {
      const parsed = Number(raw.value);
      return Number.isFinite(parsed) ? parsed : null;
    }
  }
  if (typeof raw === 'string') {
    const parsed = Number(raw);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

export function formatAreaValue(areaHectares, unit = 'ha') {
  if (!Number.isFinite(areaHectares)) return 'N/D';
  if (unit === 'm2') {
    return `${AREA_M2_FORMAT.format(areaHectares * 10000)} m²`;
  }
  return `${AREA_NUMBER_FORMAT.format(areaHectares)} ha`;
}

export function getAreaUnitToggleLabel(unit = 'ha') {
  return unit === 'ha' ? 'm²' : 'ha';
}
