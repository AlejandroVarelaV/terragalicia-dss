import React, { useEffect, useState } from 'react';
import { BACKEND_BASE_URL } from '../data/sigpacService.js';

const DAY_NAMES_GL = ['Dom', 'Lun', 'Mar', 'Mér', 'Xov', 'Ven', 'Sáb'];

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

  const formatTemp = (value) => {
    if (value == null || Number.isNaN(Number(value))) return '—';
    return `${Number(value).toFixed(1)}°C`;
  };

  const getDayName = (forecastItem) => {
    const rawDate = forecastItem?.date
      || forecastItem?.validFrom
      || forecastItem?.dateIssued
      || forecastItem?.time;
    if (!rawDate) return '—';
    const date = new Date(rawDate);
    if (Number.isNaN(date.getTime())) return '—';
    return DAY_NAMES_GL[date.getDay()] || '—';
  };

  const currentLabel = loading ? 'Cargando...' : 'Actual';

  return (
    <div className="weather-button-container">
      <button className="weather-toggle" onClick={onToggle} aria-label="Abrir tempo">☁️</button>
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
              <div className="forecast-strip">
                {forecast.slice(0, 7).map((f, i) => (
                  <div key={i} className="forecast-day">
                    <div className="forecast-day-name">{getDayName(f)}</div>
                    <div className="forecast-icon">{renderIcon(f)}</div>
                    <div className="forecast-temp">
                      {formatTemp(f.temperatureMax ?? f.temperature_max)} / {formatTemp(f.temperatureMin ?? f.temperature_min)}
                    </div>
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
