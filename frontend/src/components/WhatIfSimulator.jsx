import React, { useState } from 'react';
import { BACKEND_BASE_URL } from '../data/sigpacService.js';
import { CROP_OPTIONS, getReadableCropLabel } from '../data/uiLabels.js';

export default function WhatIfSimulator({ parcelId, onClose, authToken }) {
  const [scenarios, setScenarios] = useState([
    { cropId: 'millo', month: 4 },
    { cropId: 'pataca', month: 3 },
    { cropId: 'trigo', month: 10 },
  ]);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const updateScenario = (idx, field, value) => {
    const copy = [...scenarios];
    copy[idx][field] = value;
    setScenarios(copy);
  };

  const compare = async () => {
    if (!parcelId) {
      setError('Selecciona unha parcela no mapa primeiro');
      return;
    }
    if (!authToken) {
      setError('Selecciona unha parcela no mapa primeiro');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const body = {
        parcelId,
        scenarios: scenarios.map((s) => ({
          cropId: s.cropId,
          sowingDate: `2026-${String(s.month).padStart(2, '0')}-01`,
          irrigationMm: 0,
        })),
      };
      const res = await fetch(`${BACKEND_BASE_URL}/simulator/whatif`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const json = await res.json();
      setResults(json);
    } catch (e) {
      setError('Erro ao cargar os datos. Téntao de novo.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="whatif-modal">
      <header>
        <h3>Simulador de escenarios</h3>
        <button onClick={onClose} aria-label="Pechar">✕</button>
      </header>
      <div className="whatif-body">
        {scenarios.map((s, i) => (
          <div key={i} className="scenario-row">
            <label className="scenario-label">Cultivo</label>
            <select value={s.cropId} onChange={(e)=>updateScenario(i,'cropId',e.target.value)}>
              {CROP_OPTIONS.map((c) => <option key={c} value={c}>{getReadableCropLabel(c)}</option>)}
            </select>
            <label className="scenario-label">Mes da sementeira</label>
            <input type="range" min="1" max="12" value={s.month} onChange={(e)=>updateScenario(i,'month',Number(e.target.value))} />
            <div className="month-label">{s.month}</div>
          </div>
        ))}
        <div className="whatif-actions">
          <button onClick={compare} disabled={loading}>{loading ? 'Cargando...' : 'Comparar'}</button>
        </div>
        {error && <div className="error">{error}</div>}
        {results && (
          <div className="whatif-results">
            {(() => {
              const scenarioResults = (results.scenarios || []).map((entry) => ({
                cropId: entry.scenario?.cropId,
                score: Number(entry.prediction?.yieldIndex ?? entry.prediction?.score ?? 0),
                explanation: entry.prediction?.reason || entry.prediction?.explanation || '',
              }));
              return scenarioResults.sort((a, b) => b.score - a.score).map((r, i) => {
                const displayScore = r.score <= 1 ? r.score * 100 : r.score;
                const band = displayScore >= 70 ? 'green' : displayScore >= 40 ? 'yellow' : 'red';
                return (
                  <div key={i} className={`res ${band}`}>
                    <div className="res-top">
                      <div className="res-crop">{getReadableCropLabel(r.cropId)}</div>
                      <div className="res-score">Probabilidade de éxito: {Math.round(displayScore)}%</div>
                    </div>
                    <div className="res-bar"><span style={{ width: `${Math.max(0, Math.min(100, displayScore))}%` }} /></div>
                    <div className="res-explain">{r.explanation || 'Recomendación dispoñible no backend.'}</div>
                  </div>
                );
              });
            })()}
          </div>
        )}
      </div>
    </div>
  );
}
