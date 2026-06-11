const API = import.meta.env.VITE_API_URL || '';

async function req(path, opts = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json', ...opts.headers },
    ...opts,
  });
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json();
}

export const api = {
  createSession: (balance) => req('/api/session', { method: 'POST', body: JSON.stringify({ balance }) }),
  getSession: (sid) => req(`/api/session/${sid}`),
  deleteSession: (sid) => req(`/api/session/${sid}`, { method: 'DELETE' }),
  getAccount: (sid) => req(`/api/account/${sid}`),
  getPrices: () => req('/api/prices'),
  getPriceHistory: (inst) => req(`/api/price-history/${inst}`),
  getTickLog: (inst) => req(`/api/tick-log/${inst}`),
  getPositions: (sid) => req(`/api/positions/${sid}`),
  openPosition: (sid, data) => req(`/api/positions/${sid}`, { method: 'POST', body: JSON.stringify(data) }),
  closePosition: (sid, data) => req(`/api/positions/${sid}/close`, { method: 'POST', body: JSON.stringify(data) }),
  closeAll: (sid, inst) => req(`/api/positions/${sid}/close-all/${inst}`, { method: 'POST' }),
  getHistory: (sid) => req(`/api/history/${sid}`),
  getMetrics: (sid) => req(`/api/metrics/${sid}`),
  copilot: (text) => req('/api/copilot', { method: 'POST', body: JSON.stringify({ text }) }),
  sentiment: () => req('/api/sentiment', { method: 'POST' }),
  getDataSource: () => req('/api/data-source'),
  getConfig: () => req('/api/config'),
};

export function connectWS(onTick) {
  const ws = new WebSocket(`${API.replace(/^http/, 'ws')}/ws/ticks`);
  ws.onmessage = (e) => { try { onTick(JSON.parse(e.data)); } catch {} };
  ws.onclose = () => { setTimeout(() => connectWS(onTick), 3000); };
  ws.onerror = () => ws.close();
  return ws;
}
