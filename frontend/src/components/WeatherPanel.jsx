import React, { useEffect, useState } from 'react';
import { BACKEND_BASE_URL } from '../data/sigpacService.js';

const DAYS_GL = ['Domingo', 'Luns', 'Martes', 'Mércores', 'Xoves', 'Venres', 'Sábado'];

export default function WeatherPanel({ mapCenter, open, onToggle, onClose }) {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!mapCenter || !open) return;
    let mounted = true;
    setLoading(true);
    setError(null);
    const [lat, lon] = mapCenter;
    fetch(`${BACKEND_BASE_URL}/weather?lat=${lat}&lon=${lon}`)
      .then((r) => {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then((json) => { if (mounted) setData(json); })
      .catch(() => { if (mounted) setError('Erro ao cargar os datos. Téntao de novo.'); })
      .finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false; };
  }, [mapCenter, open]);

  const current = data?.current || null;
  const forecast = data?.forecast || [];
  const isClimatology = data?.dataQuality === 'climatological_average' || current?.dataQuality === 'climatological_average';

  const formatHumidity = (value) => {
    if (value == null) return 'N/D';
    const numeric = Number(value);
    const percentage = numeric <= 1 ? numeric * 100 : numeric;
    return `${Math.round(percentage)}%`;
  };

  const formatTemp = (value) => {
    if (value == null || Number.isNaN(Number(value))) return '—';
    return `${Number(value).toFixed(1)}°C`;
  };

  const getDayName = (validFrom) => {
    if (!validFrom) return '—';
    try {
      const d = new Date(validFrom + 'T12:00:00');
      return DAYS_GL[d.getDay()];
    } catch {
      return '—';
    }
  };

  const currentLabel = loading ? 'Cargando...' : 'Actual';

  return (
    <div className="weather-button-container">
      <button className="weather-toggle" onClick={onToggle} aria-label="Abrir tempo" title="Tempo na zona do mapa">☁️</button>
      {open && (
        <div className="weather-drawer">
          <header>
            <h3>Tempo na zona do mapa</h3>
            <div className="weather-panel-actions">
              <button type="button" className="weather-future-btn" disabled title="Próximamente: simulación do tempo" aria-label="Próximamente: simulación do tempo">
                ▶
              </button>
              <button onClick={onClose} aria-label="Pechar">✕</button>
            </div>
          </header>
          {loading && <div className="panel-loading">Cargando...</div>}
          {error && <div className="panel-error">{error}</div>}
          {isClimatology && <div className="panel-warning">Aviso: usando media climática.</div>}
          {current && (
            <div className="panel-body">
              <div className="current-row">
                <div><strong>{currentLabel}:</strong></div>
                <div>Temperatura: {formatTemp(current.temperature)}</div>
                <div>Humidade: {formatHumidity(current.relativeHumidity)}</div>
                <div>Precipitación: {current.precipitation ?? 'N/D'} mm</div>
                <div>Vento: {current.windSpeed ?? 'N/D'} m/s</div>
              </div>
            </div>
          )}
          {!loading && data && forecast.length > 0 && (
            <div className="forecast-section">
              <p className="forecast-section-title">Previsión 7 días</p>
              <table className="forecast-table">
                <thead>
                  <tr>
                    <th>Día</th>
                    <th>Máx</th>
                    <th>Mín</th>
                    <th>Prec.</th>
                  </tr>
                </thead>
                <tbody>
                  {forecast.map((day, i) => (
                    <tr key={i}>
                      <td className="forecast-day-col">{getDayName(day.validFrom)}</td>
                      <td>{formatTemp(day.temperatureMax)}</td>
                      <td>{formatTemp(day.temperatureMin)}</td>
                      <td>{day.precipitation != null ? `${Number(day.precipitation).toFixed(1)}mm` : 'N/D'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {!loading && !error && data && forecast.length === 0 && (
            <div className="panel-warning">Previsión non dispoñible de momento.</div>
          )}
        </div>
      )}
    </div>
  );
}
