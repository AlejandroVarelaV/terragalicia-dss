import React, { useState } from 'react';

// Lightweight UUID v4 generator
function uuidv4() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export default function AgroCopilot({ parcelId }) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');

  const sendMessage = async () => {
    if (!input.trim()) return;
    if (!parcelId) {
      alert('Selecciona unha parcela no mapa primeiro');
      return;
    }
    const sessionId = uuidv4();
    const msg = { role: 'user', text: input };
    setMessages((m) => [...m.slice(-4), msg]);
    setLoading(true);
    try {
      const res = await fetch('/api/v1/copilot/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input, parcelId, language: 'gl', sessionId }),
      });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const json = await res.json();
      const reply = { role: 'assistant', text: json.answer || json.message || 'Sen resposta', sources: json.sources || [] };
      setMessages((m) => [...m, reply]);
      setInput('');
    } catch (e) {
      setMessages((m) => [...m, { role: 'assistant', text: 'Erro ao cargar os datos. Téntao de novo.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`agro-copilot ${open ? 'open' : ''}`}>
      <button className="agro-toggle" onClick={() => setOpen((s) => !s)}>🌱</button>
      {open && (
        <div className="agro-drawer">
          <header>
            <h4>AgroCopilot</h4>
            <button onClick={() => setOpen(false)}>✕</button>
          </header>
          <div className="agro-messages">
            {messages.map((m, i) => (
              <div key={i} className={`msg ${m.role}`}>{m.text}{m.sources ? <div className="sources">{m.sources.join(', ')}</div> : null}</div>
            ))}
          </div>
          <div className="agro-input">
            <input placeholder="Pregunta sobre a túa parcela..." value={input} onChange={(e) => setInput(e.target.value)} />
            <button disabled={loading} onClick={sendMessage}>{loading ? '…' : 'Enviar'}</button>
          </div>
        </div>
      )}
    </div>
  );
}
