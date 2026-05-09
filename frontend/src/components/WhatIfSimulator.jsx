import React, { useState } from 'react';

const CROPS = ['millo','pataca','kiwi','albarino','mencia','grelos','trigo','centeo'];

export default function WhatIfSimulator({ parcelId, onClose }) {
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
    if (!parcelId) return alert('Selecciona unha parcela no mapa primeiro');
    setLoading(true);
    setError(null);
    try {
      const body = { parcelId, scenarios: scenarios.map(s => ({ cropId: s.cropId, sowingDate: `2026-${String(s.month).padStart(2,'0')}-01` })) };
      const res = await fetch('/api/v1/simulator/whatif', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) });
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
        <h3>What-If Simulator</h3>
        <button onClick={onClose}>✕</button>
      </header>
      <div className="whatif-body">
        {scenarios.map((s, i) => (
          <div key={i} className="scenario-row">
            <select value={s.cropId} onChange={(e)=>updateScenario(i,'cropId',e.target.value)}>
              {CROPS.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
            <input type="range" min="1" max="12" value={s.month} onChange={(e)=>updateScenario(i,'month',Number(e.target.value))} />
            <div className="month-label">{s.month}</div>
          </div>
        ))}
        <div className="whatif-actions">
          <button onClick={compare} disabled={loading}>{loading ? '…' : 'Comparar'}</button>
        </div>
        {error && <div className="error">{error}</div>}
        {results && (
          <div className="whatif-results">
            {results.sort((a,b)=>b.score-a.score).map((r,i)=> (
              <div key={i} className={`res ${r.colorBand || 'yellow'}`}>
                <div className="res-crop">{r.cropId}</div>
                <div className="res-score">{Math.round(r.score)}</div>
                <div className="res-explain">{r.reason || ''}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
