export default function ParcelPopup({ parcel, suitability = null, loading = false }) {
  const cropName = parcel?.cropName || parcel?.cultivo || 'Not assigned';
  const soilType = parcel?.soilType || 'Unknown soil';
  const areaText = parcel?.area != null ? `${Number(parcel.area).toFixed(2)} ha` : 'N/A';
  const status = parcel?.status || 'UNKNOWN';

  const statusColor = {
    PREPARED: '#22c55e',
    FALLOW:   '#9ca3af',
    PLANTED:  '#f59e0b',
    HARVESTED:'#3b82f6',
  }[status] || '#64748b';

  const statusLabel = {
    PREPARED:  'Prepared',
    FALLOW:    'Fallow',
    PLANTED:   'Planted',
    HARVESTED: 'Harvested',
  }[status] || status;

  const id = parcel?.id || parcel?.gid || parcel?.ref || 'Unknown';
  const shortId = id.length > 24 ? '…' + id.slice(-20) : id;

  const bandColor = { high: '#22c55e', medium: '#f59e0b', low: '#ef4444' };

  const suitabilitySection = loading
    ? `<div class="popup-suitability-loading">
         <span class="popup-spinner"></span>
         <span>Loading recommendations…</span>
       </div>`
    : suitability?.ranking?.length
    ? `<div class="popup-suitability">
         <p class="popup-section-title">Crop recommendations</p>
         <ol class="popup-ranking">
           ${suitability.ranking.slice(0, 3).map((item, i) => `
             <li class="popup-ranking-item">
               <span class="popup-rank-num">${i + 1}</span>
               <span class="popup-crop-id">${item.cropId.split(':').pop()}</span>
               <span class="popup-score-bar">
                 <span class="popup-score-fill" 
                   style="width:${Math.round(item.score * 100)}%;background:${bandColor[item.band] || '#64748b'}">
                 </span>
               </span>
               <span class="popup-score-pct">${Math.round(item.score * 100)}%</span>
             </li>
           `).join('')}
         </ol>
       </div>`
    : '';

  return `
    <div class="popup-card">
      <p class="popup-kicker">Parcel</p>
      <h3 title="${id}">${shortId}</h3>
      <div class="popup-status-row">
        <span class="popup-status-dot" style="background:${statusColor}"></span>
        <span class="popup-status-label">${statusLabel}</span>
      </div>
      <dl>
        <div><dt>Crop</dt><dd>${cropName}</dd></div>
        <div><dt>Soil</dt><dd>${soilType}</dd></div>
        <div><dt>Area</dt><dd>${areaText}</dd></div>
      </dl>
      ${suitabilitySection}
      <div class="popup-footer">
        <span class="popup-source-badge">
          ${parcel?.source === 'seed-fallback' ? 'Seed data' : 'Live data'}
        </span>
      </div>
    </div>
  `;
}