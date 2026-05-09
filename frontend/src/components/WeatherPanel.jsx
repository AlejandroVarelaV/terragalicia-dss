import React, { useEffect, useState } from 'react';

export default function WeatherPanel({ parcelId, onClose }) {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!parcelId) return;
    let mounted = true;
    setLoading(true);
    setError(null);
    fetch(`/api/v1/weather?parcelId=${encodeURIComponent(parcelId)}`)
      .then((r) => {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then((json) => { if (mounted) setData(json); })
      .catch((e) => { if (mounted) setError('Erro ao cargar os datos. Téntao de novo.'); })
      .finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false; };
  }, [parcelId]);

  if (!parcelId) return null;

  const isClimatology = data && data.dataQuality === 'climatological_average';

  const renderIcon = (f) => {
    if (!f) return '⛅';
    if (f.temperature < 2) return '🌨️';
    if ((f.precipitation || 0) > 5) return '🌧️';
    if ((f.precipitation || 0) === 0) return '☀️';
    return '⛅';
  };

  return (
    <aside className="weather-panel">
      <header>
        <h3>Weather</h3>
        <button onClick={onClose} aria-label="Close">✕</button>
      </header>
      {loading && <div className="panel-loading">Cargando...</div>}
      {error && <div className="panel-error">{error}</div>}
      {isClimatology && <div className="panel-warning">Aviso: usando media climática.</div>}
      {data && (
        <div className="panel-body">
          <div className="current-row">
            <div>Temp: {data.temperature ?? 'N/A'}°C</div>
            <div>RH: {Math.round((data.relativeHumidity||0)*100)}%</div>
            <div>Precip: {data.precipitation ?? 'N/A'} mm</div>
            <div>Wind: {data.windSpeed ?? 'N/A'} m/s</div>
          </div>
          <div className="forecast-strip">
            {(data.forecast || []).slice(0,7).map((f, i) => (
              <div key={i} className="forecast-day">
                <div className="forecast-icon">{renderIcon(f)}</div>
                <div className="forecast-date">{f.date}</div>
                <div className="forecast-temp">{f.temperature_max}/{f.temperature_min}°C</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </aside>
  );
}
