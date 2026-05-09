import React, { useEffect, useState } from 'react';
import { BACKEND_BASE_URL } from '../data/sigpacService.js';

// Lightweight UUID v4 generator
function uuidv4() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export default function AgroCopilot({ parcelId, authToken }) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [infoMessage, setInfoMessage] = useState('');

  useEffect(() => {
    if (parcelId) {
      setInfoMessage('');
      return;
    }
    setInfoMessage('Selecciona unha parcela no mapa primeiro.');
  }, [parcelId]);

  const sendMessage = async () => {
    if (!input.trim()) return;
    if (!parcelId) {
      setInfoMessage('Selecciona unha parcela no mapa primeiro');
      return;
    }
    if (!authToken) {
      setInfoMessage('Selecciona unha parcela no mapa primeiro');
      return;
    }
    const sessionId = uuidv4();
    const msg = { role: 'user', text: input };
    setMessages((m) => [...m, msg].slice(-5));
    setLoading(true);
    setInfoMessage('');
    try {
      const res = await fetch(`${BACKEND_BASE_URL}/copilot/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify({ message: input, parcelId, language: 'gl', sessionId }),
      });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const json = await res.json();
      const reply = { role: 'assistant', text: json.answer || json.message || 'Sen resposta', sources: json.references || json.sources || [] };
      setMessages((m) => [...m, reply].slice(-5));
      setInput('');
    } catch (e) {
      setMessages((m) => [...m, { role: 'assistant', text: 'Erro ao cargar os datos. Téntao de novo.' }].slice(-5));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`agro-copilot ${open ? 'open' : ''}`}>
      <button className="agro-toggle" onClick={() => setOpen((s) => !s)} aria-label="Abrir Axente Agronómico" title="Axente Agronómico">🌱</button>
      {open && (
        <div className="agro-drawer">
          <header>
            <h4>Axente Agronómico</h4>
            <button onClick={() => setOpen(false)} aria-label="Pechar">✕</button>
          </header>
          {infoMessage && <div className="agro-empty-state">{infoMessage}</div>}
          <div className="agro-messages">
            {messages.map((m, i) => (
              <div key={i} className={`msg ${m.role}`}>{m.text}{m.sources ? <div className="sources">{m.sources.join(', ')}</div> : null}</div>
            ))}
          </div>
          <div className="agro-input">
            <input placeholder="Pregunta sobre a túa parcela..." value={input} onChange={(e) => setInput(e.target.value)} />
            <button disabled={loading} onClick={sendMessage}>{loading ? 'Cargando...' : 'Enviar'}</button>
          </div>
        </div>
      )}
    </div>
  );
}
