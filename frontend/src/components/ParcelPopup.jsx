export default function ParcelPopup({ parcel }) {
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
      <div class="popup-footer">
        <span class="popup-source-badge">${parcel?.source === 'seed-fallback' ? 'Seed data' : 'Live data'}</span>
      </div>
    </div>
  `;
}