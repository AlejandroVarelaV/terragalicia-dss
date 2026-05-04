export default function ParcelPopup({ parcel }) {
  const cropName = parcel?.cropName || parcel?.cultivo || 'Not assigned';
  const soilType = parcel?.soilType || 'Unknown soil';
  const areaText = parcel?.area != null ? `${Number(parcel.area).toFixed(2)} ha` : 'N/A';

  return `
    <div class="popup-card">
      <p class="popup-kicker">Parcel</p>
      <h3>Parcel ID: ${parcel?.id || parcel?.gid || parcel?.ref || 'Unknown'}</h3>
      <dl>
        <div><dt>Crop</dt><dd>${cropName}</dd></div>
        <div><dt>Soil</dt><dd>${soilType}</dd></div>
        <div><dt>Status</dt><dd>${parcel.status}</dd></div>
        <div><dt>Area</dt><dd>${areaText}</dd></div>
      </dl>
    </div>
  `;
}