import { useState, useEffect, useCallback } from 'react';
import { useSession } from '../App';
import { api, connectWS } from '../api';

export default function Dashboard() {
  const { sid, acct, prices, setPrices, refreshAcct } = useSession();
  const [positions, setPositions] = useState([]);
  const [metrics, setMetrics] = useState({});
  const [tickLog, setTickLog] = useState([]);
  const [selectedInst, setSelectedInst] = useState('EUR_USD');
  const [sentiment, setSentiment] = useState(null);
  const [copilotText, setCopilotText] = useState('');
  const [copilotResult, setCopilotResult] = useState(null);
  const [loading, setLoading] = useState(false);

  // WebSocket for live ticks
  useEffect(() => {
    const ws = connectWS((msg) => {
      if (msg.type === 'tick') {
        setPrices((prev) => ({ ...prev, [msg.instrument]: { bid: msg.bid, ask: msg.ask } }));
        if (msg.instrument === selectedInst) {
          setTickLog((prev) => [...prev.slice(-99), { time: new Date().toLocaleTimeString(), bid: msg.bid, ask: msg.ask, mid: (msg.bid + msg.ask) / 2 }]);
        }
      }
    });
    return () => ws.close();
  }, [selectedInst, setPrices]);

  // Initial data load
  useEffect(() => {
    (async () => {
      try {
        const [p, pos, m] = await Promise.all([api.getPrices(), api.getPositions(sid), api.getMetrics(sid)]);
        setPrices(p);
        setPositions(pos);
        setMetrics(m);
        if (p[selectedInst]) {
          const log = await api.getTickLog(selectedInst);
          setTickLog(log);
        }
      } catch {}
    })();
  }, [sid, selectedInst, setPrices]);

  const refresh = useCallback(async () => {
    try {
      const [pos, m] = await Promise.all([api.getPositions(sid), api.getMetrics(sid)]);
      setPositions(pos);
      setMetrics(m);
      refreshAcct();
    } catch {}
  }, [sid, refreshAcct]);

  useEffect(() => { const t = setInterval(refresh, 3000); return () => clearInterval(t); }, [refresh]);

  const handleTrade = async (direction) => {
    setLoading(true);
    try {
      await api.openPosition(sid, { instrument: selectedInst, direction, volume_lots: 0.1 });
      refresh();
    } catch {}
    setLoading(false);
  };

  const handleCopilot = async () => {
    if (!copilotText.trim()) return;
    setLoading(true);
    try {
      const result = await api.copilot(copilotText);
      setCopilotResult(result);
    } catch {}
    setLoading(false);
  };

  const handleCopilotExecute = async () => {
    if (!copilotResult || copilotResult.error) return;
    setLoading(true);
    try {
      await api.openPosition(sid, {
        instrument: copilotResult.instrument,
        direction: copilotResult.direction,
        volume_lots: copilotResult.volume_lots,
        stop_loss: copilotResult.stop_loss || 0,
        take_profit: copilotResult.take_profit || 0,
      });
      setCopilotResult(null);
      setCopilotText('');
      refresh();
    } catch {}
    setLoading(false);
  };

  const fetchSentiment = async () => {
    setLoading(true);
    try { setSentiment(await api.sentiment()); } catch {}
    setLoading(false);
  };

  const p = prices[selectedInst] || {};
  const instList = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'AUD_USD', 'USD_CAD'];

  return (
    <div className="space-y-4 max-w-7xl mx-auto">
      {/* Metrics row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Equity', value: `$${(acct?.equity || 0).toLocaleString(undefined, {minimumFractionDigits:2})}` },
          { label: 'Balance', value: `$${(acct?.balance || 0).toLocaleString(undefined, {minimumFractionDigits:2})}` },
          { label: 'Floating P&L', value: `$${((acct?.equity||0)-(acct?.balance||0)).toFixed(2)}`, cls: (acct?.equity||0) >= (acct?.balance||0) ? 'text-green' : 'text-red' },
          { label: 'Open Positions', value: positions.length },
        ].map(({ label, value, cls }) => (
          <div key={label} className="bg-dark-800 border border-gray-700/50 rounded-xl p-3">
            <div className="text-xs text-gray-500 mb-1">{label}</div>
            <div className={`text-lg font-semibold font-mono ${cls || 'text-white'}`}>{value}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Left: Price feed + chart */}
        <div className="lg:col-span-2 space-y-4">
          {/* Instrument selector */}
          <div className="bg-dark-800 border border-gray-700/50 rounded-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="text-xs text-gray-500 uppercase tracking-wider">Market Watch</div>
              <select value={selectedInst} onChange={(e) => setSelectedInst(e.target.value)}
                className="bg-dark-700 border border-gray-600 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-accent">
                {instList.map((i) => <option key={i} value={i}>{i.replace('_', '/')}</option>)}
              </select>
            </div>
            <div className="flex items-center gap-6 mb-4">
              <div>
                <div className="text-xs text-gray-500">Bid</div>
                <div className="text-xl font-mono font-bold text-red">{p.bid?.toFixed(5) || '—'}</div>
              </div>
              <div>
                <div className="text-xs text-gray-500">Ask</div>
                <div className="text-xl font-mono font-bold text-green">{p.ask?.toFixed(5) || '—'}</div>
              </div>
              <div className="ml-auto flex gap-2">
                <button onClick={() => handleTrade('BUY')} disabled={loading}
                  className="px-5 py-2 bg-green hover:bg-green-muted text-white font-semibold rounded-lg text-sm disabled:opacity-50">
                  BUY
                </button>
                <button onClick={() => handleTrade('SELL')} disabled={loading}
                  className="px-5 py-2 bg-red hover:bg-red-muted text-white font-semibold rounded-lg text-sm disabled:opacity-50">
                  SELL
                </button>
              </div>
            </div>

            {/* Tick log */}
            <div className="h-48 overflow-y-auto font-mono text-xs">
              {tickLog.length === 0 && <div className="text-gray-600">Waiting for ticks...</div>}
              {[...tickLog].reverse().map((t, i) => (
                <div key={i} className="flex justify-between py-0.5 border-b border-gray-800/50">
                  <span className="text-gray-500">{t.time}</span>
                  <span className="text-red">{t.bid?.toFixed(5)}</span>
                  <span className="text-green">{t.ask?.toFixed(5)}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Open positions */}
          <div className="bg-dark-800 border border-gray-700/50 rounded-xl p-4">
            <div className="text-xs text-gray-500 uppercase tracking-wider mb-3">Open Positions</div>
            {positions.length === 0 ? (
              <div className="text-gray-600 text-sm">No open positions</div>
            ) : (
              <div className="space-y-2">
                {positions.map((pos) => (
                  <div key={pos.ticket_id} className="flex items-center justify-between bg-dark-700 rounded-lg px-3 py-2">
                    <div className="flex items-center gap-3">
                      <span className={`text-xs font-bold ${pos.direction === 'BUY' ? 'text-green' : 'text-red'}`}>{pos.direction}</span>
                      <span className="text-sm">{pos.instrument.replace('_', '/')}</span>
                      <span className="text-xs text-gray-400">{pos.volume_lots} lots</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-mono text-gray-400">@ {pos.entry_price?.toFixed(5)}</span>
                      <button onClick={async () => { await api.closePosition(sid, { ticket_id: pos.ticket_id, exit_price: pos.current_price }); refresh(); }}
                        className="text-xs text-red hover:text-red-muted">Close</button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right: Co-Pilot + Sentiment */}
        <div className="space-y-4">
          {/* Co-Pilot */}
          <div className="bg-dark-800 border border-gray-700/50 rounded-xl p-4">
            <div className="text-xs text-gray-500 uppercase tracking-wider mb-3">AI Co-Pilot</div>
            <textarea value={copilotText} onChange={(e) => setCopilotText(e.target.value)}
              placeholder='e.g. "Buy 1 lot EUR/USD, SL 1.0800, TP 1.1000"'
              className="w-full bg-dark-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white resize-none h-20 focus:outline-none focus:border-accent mb-2" />
            <button onClick={handleCopilot} disabled={loading}
              className="w-full py-2 bg-accent hover:bg-accent-hover text-white text-sm font-medium rounded-lg disabled:opacity-50">
              Parse Trade
            </button>
            {copilotResult && !copilotResult.error && (
              <div className="mt-3 bg-dark-700 rounded-lg p-3 text-xs space-y-1">
                <div><span className="text-gray-500">Action:</span> <span className="text-white">{copilotResult.action}</span></div>
                <div><span className="text-gray-500">Instrument:</span> <span className="text-white">{copilotResult.instrument?.replace('_','/')}</span></div>
                <div><span className="text-gray-500">Direction:</span> <span className={copilotResult.direction === 'BUY' ? 'text-green' : 'text-red'}>{copilotResult.direction}</span></div>
                <div><span className="text-gray-500">Volume:</span> <span className="text-white">{copilotResult.volume_lots} lots</span></div>
                <button onClick={handleCopilotExecute} disabled={loading}
                  className="w-full mt-2 py-1.5 bg-green hover:bg-green-muted text-white text-xs font-medium rounded-lg disabled:opacity-50">
                  Execute Trade
                </button>
              </div>
            )}
          </div>

          {/* Sentiment */}
          <div className="bg-dark-800 border border-gray-700/50 rounded-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="text-xs text-gray-500 uppercase tracking-wider">Market Sentiment</div>
              <button onClick={fetchSentiment} disabled={loading}
                className="text-xs text-accent hover:text-accent-hover disabled:opacity-50">
                Refresh
              </button>
            </div>
            {sentiment ? (
              <div>
                <div className={`text-lg font-bold ${
                  sentiment.sentiment === 'BULLISH' ? 'text-green' :
                  sentiment.sentiment === 'BEARISH' ? 'text-red' : 'text-gray-400'
                }`}>{sentiment.sentiment}</div>
                <div className="text-xs text-gray-500 mt-1 max-h-32 overflow-y-auto">{sentiment.headlines}</div>
              </div>
            ) : (
              <div className="text-gray-600 text-sm">Click Refresh to analyze</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
