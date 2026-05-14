import {
  getAreaHectares,
  getAreaUnitToggleLabel,
  getCropValue,
  getParcelTitle,
  getReadableCropLabel,
  getReadableSoilLabel,
  getReadableStatusLabel,
  getReadableUsoSigpac,
  getSoilValue,
  getStatusValue,
  formatAreaValue,
} from '../data/uiLabels.js';

export default function ParcelPopup({ parcel, suitability = null, loading = false }) {
  const title = getParcelTitle(parcel);
  const cropValue = getCropValue(parcel);
  const soilValue = getSoilValue(parcel);
  const areaHectares = getAreaHectares(parcel);
  const status = getStatusValue(parcel);
  const statusColor = {
    PREPARED: '#22c55e',
    FALLOW: '#9ca3af',
    PLANTED: '#f59e0b',
    HARVESTED: '#3b82f6',
  }[status] || '#64748b';
  const statusLabel = getReadableStatusLabel(status);
  const cropName = cropValue ? getReadableCropLabel(cropValue) : 'Sen asignar';
  const soilName = soilValue ? getReadableSoilLabel(soilValue) : 'Sen asignar';
  const parcelId = parcel?.id || parcel?.gid || parcel?.ref || 'Unknown';
  const pendienteRaw = parcel?.pendiente_media ?? parcel?.slope ?? parcel?.slope_percent ?? null;
  const pendienteDisplay = Number.isFinite(Number(pendienteRaw)) ? `${(Number(pendienteRaw) / 10).toFixed(1)}%` : 'N/D';
  const altitud = parcel?.altitud ?? parcel?.elevation ?? null;
  const altitudDisplay = altitud != null ? `${altitud} m` : 'N/D';
  const uso = parcel?.uso_sigpac ?? parcel?.landUse ?? 'N/D';
  const coefReg = parcel?.coef_regadio ?? parcel?.coef_regadio ?? null;
  const coefRegDisplay = (coefReg !== null && coefReg !== undefined && Number(coefReg) > 0) ? 'Sí' : 'Non';
  const bandColor = { high: '#22c55e', medium: '#f59e0b', low: '#ef4444' };
  const sourceLabel = parcel?.source === 'seed-fallback' ? 'Datos de proba' : 'Datos reais';

  const suitabilitySection = (() => {
    if (loading) {
      return `<div class="popup-suitability-loading">
         <span class="popup-spinner"></span>
         <span>Cargando recomendacións...</span>
       </div>`;
    }
    if (suitability?.excludedReason) {
      return `<div class="popup-suitability-excluded">
        <p class="popup-section-title">Recomendación</p>
        <div class="popup-excluded-reason">${suitability.excludedReason}</div>
      </div>`;
    }
    if (suitability?.error) {
      return `<div class="popup-suitability-error">Erro: ${suitability.error}</div>`;
    }
    const ranking = suitability?.ranking || [];
    if (!ranking.length) return '';

    const top = ranking[0];
    const topCropId = top.cropId?.split(':').pop?.() || top.cropId || '';
    const topLabel = getReadableCropLabel(topCropId);
    const topScore = top.score <= 1 ? top.score * 100 : top.score;
    const topBreakdown = top.breakdown || {};

    const otherItems = ranking.slice(1).map((item) => {
      const cropId = item.cropId?.split(':').pop?.() || item.cropId || '';
      const cropLabel = getReadableCropLabel(cropId);
      const scoreValue = item.score <= 1 ? item.score * 100 : item.score;
      return `
        <li class="popup-ranking-item">
          <span class="popup-rank-num">${""}</span>
          <span class="popup-crop-id">${cropLabel}</span>
          <span class="popup-score-bar"><span class="popup-score-fill" style="width:${Math.max(0, Math.min(100, scoreValue))}%;background:${bandColor[item.band || item.colorBand] || '#64748b'}"></span></span>
          <span class="popup-score-pct">${Math.round(scoreValue)}%</span>
        </li>`;
    }).join('');

    const expandBtn = otherItems ? `<button type="button" class="suitability-expand-btn" title="Ver ranking completo">+</button>` : '';
    return `<div class="popup-suitability">
      <p class="popup-section-title">Recomendación</p>
      <div class="popup-top-recommendation">
        <span class="popup-crop-id">${topLabel}</span>
        <span class="popup-score-pct">${Math.round(topScore)}%</span>
        ${expandBtn}
      </div>
      <div class="popup-ranking-full" style="display:none;">
        <ol class="popup-ranking">
          ${otherItems}
        </ol>
      </div>
    </div>`;
  })();

  const areaMarkup = Number.isFinite(areaHectares)
    ? `<div><dt>Área</dt><dd>
        <span class="popup-area-row">
          <span class="popup-area-value" data-area-hectares="${areaHectares}" data-area-unit="ha">${formatAreaValue(areaHectares, 'ha')}</span>
          <button type="button" class="popup-area-toggle" data-area-toggle="true" data-area-hectares="${areaHectares}" data-area-unit="ha">${getAreaUnitToggleLabel('ha')}</button>
        </span>
      </dd></div>`
    : `<div><dt>Área</dt><dd>N/D</dd></div>`;

  return `
    <div class="popup-card">
      <p class="popup-kicker">Parcela</p>
      <h3 title="${title}">${title}</h3>
      <div class="popup-status-row">
        <span class="popup-status-dot" style="background:${statusColor}"></span>
        <span class="popup-status-label">${statusLabel}</span>
      </div>
      <dl>
        <div><dt>Cultivo</dt><dd>${cropName || 'Sen asignar'}</dd></div>
        <div><dt>Solo</dt><dd>${soilName || 'Sen asignar'}</dd></div>
        ${areaMarkup}
        <div><dt>Pendiente</dt><dd>${pendienteDisplay}</dd></div>
        <div><dt>Altitud</dt><dd>${altitudDisplay}</dd></div>
        <div><dt>Uso SIGPAC</dt><dd>${getReadableUsoSigpac(uso) || uso}</dd></div>
        <div><dt>Regadío</dt><dd>${coefRegDisplay}</dd></div>
      </dl>
      ${suitabilitySection}
      <div class="popup-controls">
        <button class="simulate-btn" data-parcel-id="${parcelId}">🔬 Simular escenarios</button>
        <label for="status-select">Estado:</label>
        <select id="status-select" class="status-select" data-parcel-id="${parcelId}">
          <option value="PREPARED" ${status === 'PREPARED' ? 'selected' : ''}>🔧 Preparada</option>
          <option value="FALLOW" ${status === 'FALLOW' ? 'selected' : ''}>💤 Barbecho</option>
          <option value="PLANTED" ${status === 'PLANTED' ? 'selected' : ''}>🌱 Plantada</option>
          <option value="HARVESTED" ${status === 'HARVESTED' ? 'selected' : ''}>🌾 Colleitada</option>
        </select>
      </div>
      <div class="popup-footer">
        <span class="popup-source-badge">${sourceLabel}</span>
      </div>
    </div>
  `;
}