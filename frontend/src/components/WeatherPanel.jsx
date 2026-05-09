import React, { useEffect, useState } from 'react';
import { BACKEND_BASE_URL } from '../data/sigpacService.js';

export default function WeatherPanel({ mapCenter, authToken }) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    if (!mapCenter || !authToken || !open) return;
    let mounted = true;
    setLoading(true);
    setError(null);
    const [lat, lon] = mapCenter;
    fetch(`${BACKEND_BASE_URL}/weather?lat=${lat}&lon=${lon}`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
    })
      .then((r) => {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then((json) => { if (mounted) setData(json); })
      .catch(() => { if (mounted) setError('Erro ao cargar os datos. Téntao de novo.'); })
      .finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false; };
  }, [mapCenter, authToken, open]);

  const current = data?.current || null;
  const forecast = data?.forecast || [];
  const isClimatology = data?.dataQuality === 'climatological_average' || current?.dataQuality === 'climatological_average';

  const renderIcon = (f) => {
    if (!f) return '⛅';
    const temperature = Number(f.temperatureMax ?? f.temperatureMin ?? f.temperature ?? 0);
    if (temperature < 2) return '🌨️';
    if ((Number(f.precipitation ?? 0)) > 5) return '🌧️';
    if ((Number(f.precipitation ?? 0)) === 0) return '☀️';
    return '⛅';
  };

  const formatHumidity = (value) => {
    if (value == null) return 'N/D';
    const numeric = Number(value);
    const percentage = numeric <= 1 ? numeric * 100 : numeric;
    return `${Math.round(percentage)}%`;
  };

  const formatDate = (value) => {
    if (!value) return 'N/D';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return date.toLocaleDateString('gl-ES', { weekday: 'short', day: '2-digit', month: 'short' });
  };

  const currentLabel = loading ? 'Cargando...' : 'Actual';

  return (
    <div className="weather-button-container">
      <button className="weather-toggle" onClick={() => setOpen((s) => !s)} aria-label="Abrir tempo">☁️</button>
      {open && (
        <div className={`weather-drawer ${collapsed ? 'is-collapsed' : ''}`}>
          <header>
            <h3>Tempo na zona do mapa</h3>
            <div className="weather-panel-actions">
              <button type="button" onClick={() => setCollapsed((currentState) => !currentState)} aria-label={collapsed ? 'Expandir panel' : 'Contraer panel'}>
                {collapsed ? '◀' : '▶'}
              </button>
              <button onClick={() => setOpen(false)} aria-label="Pechar">✕</button>
            </div>
          </header>
          {!collapsed && loading && <div className="panel-loading">Cargando...</div>}
          {!collapsed && error && <div className="panel-error">{error}</div>}
          {!collapsed && isClimatology && <div className="panel-warning">Aviso: usando media climática.</div>}
          {!collapsed && current && (
            <div className="panel-body">
              <div className="current-row">
                <div><strong>{currentLabel}:</strong></div>
                <div>Temperatura: {current.temperature ?? 'N/D'}°C</div>
                <div>Humidade: {formatHumidity(current.relativeHumidity)}</div>
                <div>Precipitación: {current.precipitation ?? 'N/D'} mm</div>
                <div>Vento: {current.windSpeed ?? 'N/D'} m/s</div>
              </div>
              <div className="forecast-strip">
                {forecast.slice(0, 7).map((f, i) => (
                  <div key={i} className="forecast-day">
                    <div className="forecast-icon">{renderIcon(f)}</div>
                    <div className="forecast-date">{formatDate(f.validFrom || f.date)}</div>
                    <div className="forecast-temp">{f.temperatureMax ?? f.temperature_max ?? 'N/D'}/{f.temperatureMin ?? f.temperature_min ?? 'N/D'}°C</div>
                    <div className="forecast-label">Previsión</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
