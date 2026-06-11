import { useState, useEffect, useCallback } from 'react';
import { useSession } from '../App';
import { api } from '../api';

const instruments = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'AUD_USD', 'USD_CAD'];

function ManualTab() {
  const { sid, prices, refreshAcct } = useSession();
  const [instrument, setInstrument] = useState('EUR_USD');
  const [direction, setDirection] = useState('BUY');
  const [volume, setVolume] = useState(0.1);
  const [sl, setSl] = useState(0);
  const [tp, setTp] = useState(0);
  const [loading, setLoading] = useState(false);
  const [positions, setPositions] = useState([]);
  const [history, setHistory] = useState([]);

  const refresh = useCallback(async () => {
    try {
      const [p, h] = await Promise.all([api.getPositions(sid), api.getHistory(sid)]);
      setPositions(p);
      setHistory(h);
      refreshAcct();
    } catch {}
  }, [sid, refreshAcct]);

  useEffect(() => { refresh(); const t = setInterval(refresh, 2000); return () => clearInterval(t); }, [refresh]);

  const handleTrade = async () => {
    setLoading(true);
    try {
      await api.openPosition(sid, { instrument, direction, volume_lots: volume, stop_loss: sl, take_profit: tp });
      refresh();
    } catch {}
    setLoading(false);
  };

  const handleClose = async (ticketId) => {
    const pos = positions.find(p => p.ticket_id === ticketId);
    if (!pos) return;
    setLoading(true);
    try {
      await api.closePosition(sid, { ticket_id: ticketId, exit_price: pos.current_price });
      refresh();
    } catch {}
    setLoading(false);
  };

  const p = prices[instrument] || {};
  const spread = p.ask && p.bid ? (p.ask - p.bid).toFixed(5) : '—';

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {/* Order form */}
      <div className="bg-dark-800 border border-gray-700/50 rounded-xl p-5">
        <div className="text-xs text-gray-500 uppercase tracking-wider mb-4">Place Trade</div>
        <div className="grid grid-cols-2 gap-3 mb-3">
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Instrument</label>
            <select value={instrument} onChange={(e) => setInstrument(e.target.value)}
              className="w-full bg-dark-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-accent">
              {instruments.map((i) => <option key={i} value={i}>{i.replace('_','/')}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Direction</label>
            <select value={direction} onChange={(e) => setDirection(e.target.value)}
              className="w-full bg-dark-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-accent">
              <option value="BUY">BUY</option>
              <option value="SELL">SELL</option>
            </select>
          </div>
        </div>
        <div className="grid grid-cols-3 gap-3 mb-3">
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Lots</label>
            <input type="number" value={volume} onChange={(e) => setVolume(Number(e.target.value))}
              min={0.01} max={100} step={0.01}
              className="w-full bg-dark-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-accent" />
          </div>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Stop Loss</label>
            <input type="number" value={sl} onChange={(e) => setSl(Number(e.target.value))} step={0.0001}
              className="w-full bg-dark-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-accent" />
          </div>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Take Profit</label>
            <input type="number" value={tp} onChange={(e) => setTp(Number(e.target.value))} step={0.0001}
              className="w-full bg-dark-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-accent" />
          </div>
        </div>
        <div className="flex gap-2 text-xs text-gray-400 mb-4 font-mono">
          <span>Bid {p.bid?.toFixed(5) || '—'}</span>
          <span>Ask {p.ask?.toFixed(5) || '—'}</span>
          <span>Spread {spread}</span>
        </div>
        <button onClick={handleTrade} disabled={loading}
          className={`w-full py-2.5 font-semibold rounded-lg text-sm text-white disabled:opacity-50 ${
            direction === 'BUY' ? 'bg-green hover:bg-green-muted' : 'bg-red hover:bg-red-muted'
          }`}>
          Execute {direction}
        </button>
      </div>

      {/* Trade summary */}
      <div className="bg-dark-800 border border-gray-700/50 rounded-xl p-5">
        <div className="text-xs text-gray-500 uppercase tracking-wider mb-4">Open Positions ({positions.length})</div>
        {positions.length === 0 ? (
          <div className="text-gray-600 text-sm">No open positions</div>
        ) : (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {positions.map((pos) => {
              const pnl = pos.direction === 'BUY'
                ? (pos.current_price - pos.entry_price) * pos.volume_lots * 100000
                : (pos.entry_price - pos.current_price) * pos.volume_lots * 100000;
              return (
                <div key={pos.ticket_id} className="flex items-center justify-between bg-dark-700 rounded-lg px-3 py-2">
                  <div className="flex items-center gap-3">
                    <span className={`text-xs font-bold ${pos.direction === 'BUY' ? 'text-green' : 'text-red'}`}>{pos.direction}</span>
                    <span className="text-sm">{pos.instrument.replace('_','/')}</span>
                    <span className="text-xs text-gray-400">{pos.volume_lots} lots</span>
                    <span className={`text-xs font-mono ${pnl >= 0 ? 'text-green' : 'text-red'}`}>${pnl.toFixed(2)}</span>
                  </div>
                  <button onClick={() => handleClose(pos.ticket_id)} disabled={loading}
                    className="text-xs text-red hover:text-red-muted px-2 py-1 border border-red/30 rounded disabled:opacity-50">
                    Close
                  </button>
                </div>
              );
            })}
          </div>
        )}

        <div className="text-xs text-gray-500 uppercase tracking-wider mt-4 mb-2">Recent Trades</div>
        {history.length === 0 ? (
          <div className="text-gray-600 text-sm">No closed trades yet</div>
        ) : (
          <div className="space-y-1 max-h-40 overflow-y-auto">
            {history.slice(0, 5).map((t, i) => (
              <div key={i} className="flex justify-between text-xs py-1 border-b border-gray-800/50">
                <span className="text-gray-400">#{t.ticket_id} {t.instrument?.replace('_','/')} <span className={t.direction === 'BUY' ? 'text-green' : 'text-red'}>{t.direction}</span></span>
                <span className={`font-mono ${t.profit_loss >= 0 ? 'text-green' : 'text-red'}`}>${t.profit_loss?.toFixed(2)}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function CopilotTab() {
  const { sid, refreshAcct } = useSession();
  const [text, setText] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleParse = async () => {
    if (!text.trim()) return;
    setLoading(true);
    try { setResult(await api.copilot(text)); } catch {}
    setLoading(false);
  };

  const handleExecute = async () => {
    if (!result || result.error) return;
    setLoading(true);
    try {
      if (result.action === 'CLOSE_ALL') {
        await api.closeAll(sid, result.instrument);
      } else {
        await api.openPosition(sid, {
          instrument: result.instrument,
          direction: result.direction,
          volume_lots: result.volume_lots,
          stop_loss: result.stop_loss || 0,
          take_profit: result.take_profit || 0,
        });
      }
      setResult(null);
      setText('');
      refreshAcct();
    } catch {}
    setLoading(false);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <div className="bg-dark-800 border border-gray-700/50 rounded-xl p-5">
        <div className="text-xs text-gray-500 uppercase tracking-wider mb-3">Trade Instruction</div>
        <p className="text-xs text-gray-400 mb-3">Agent A parses natural language into structured trade parameters.</p>
        <textarea value={text} onChange={(e) => setText(e.target.value)}
          placeholder='e.g. "Buy 2 lots of GBP/USD, stop loss 1.2650, take profit 1.2800"'
          className="w-full bg-dark-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white resize-none h-24 focus:outline-none focus:border-accent mb-3" />
        <button onClick={handleParse} disabled={loading}
          className="w-full py-2 bg-accent hover:bg-accent-hover text-white text-sm font-medium rounded-lg disabled:opacity-50">
          {loading ? 'Parsing...' : 'Parse with AI'}
        </button>
      </div>

      <div className="bg-dark-800 border border-gray-700/50 rounded-xl p-5">
        <div className="text-xs text-gray-500 uppercase tracking-wider mb-3">Parsed Parameters</div>
        {!result ? (
          <div className="text-gray-600 text-sm text-center py-8">Enter a trade instruction to see parsed parameters</div>
        ) : result.error ? (
          <div className="text-red text-sm">Error: {result.error}</div>
        ) : (
          <div>
            <div className="grid grid-cols-3 gap-3 mb-4">
              <div className="bg-dark-700 rounded-lg p-3 text-center">
                <div className="text-xs text-gray-500">Instrument</div>
                <div className="text-sm font-semibold text-accent">{result.instrument?.replace('_','/')}</div>
              </div>
              <div className="bg-dark-700 rounded-lg p-3 text-center">
                <div className="text-xs text-gray-500">Action</div>
                <div className={`text-sm font-semibold ${result.action === 'CLOSE_ALL' ? 'text-red' : 'text-green'}`}>{result.action}</div>
              </div>
              <div className="bg-dark-700 rounded-lg p-3 text-center">
                <div className="text-xs text-gray-500">Direction</div>
                <div className={`text-sm font-semibold ${result.direction === 'BUY' ? 'text-green' : 'text-red'}`}>{result.direction}</div>
              </div>
            </div>
            <div className="space-y-2 text-sm mb-4">
              <div className="flex justify-between"><span className="text-gray-500">Volume</span><span className="font-mono">{result.volume_lots} lots</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Stop Loss</span><span className="font-mono">{result.stop_loss > 0 ? result.stop_loss.toFixed(5) : 'Not set'}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Take Profit</span><span className="font-mono">{result.take_profit > 0 ? result.take_profit.toFixed(5) : 'Not set'}</span></div>
            </div>
            <div className="flex gap-2">
              <button onClick={handleExecute} disabled={loading}
                className="flex-1 py-2 bg-green hover:bg-green-muted text-white text-sm font-medium rounded-lg disabled:opacity-50">
                {result.action === 'CLOSE_ALL' ? 'Close All' : 'Approve & Execute'}
              </button>
              <button onClick={() => setResult(null)}
                className="px-4 py-2 bg-dark-700 border border-gray-600 text-gray-400 text-sm rounded-lg hover:text-white">
                Reject
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function AutonomousTab() {
  const { sid, refreshAcct } = useSession();
  const [active, setActive] = useState(false);
  const [sentiment, setSentiment] = useState(null);
  const [smaSignal, setSmaSignal] = useState(null);
  const [autoLog, setAutoLog] = useState([]);
  const [loading, setLoading] = useState(false);

  const refreshSentiment = async () => {
    setLoading(true);
    try { setSentiment(await api.sentiment()); } catch {}
    setLoading(false);
  };

  const checkSignal = async () => {
    try { setSmaSignal(await api.getSmaSignal()); } catch {}
  };

  const runAutoTrade = async () => {
    if (!active) return;
    try {
      const result = await api.autoTrade(sid);
      if (result.traded) {
        setAutoLog(prev => [
          `[AUTO] ${result.direction} 0.1 EUR/USD @ ${result.entry_price?.toFixed(5)} | SL ${result.stop_loss?.toFixed(5)} | TP ${result.take_profit?.toFixed(5)} | #${result.ticket_id}`,
          ...prev.slice(0, 14),
        ]);
        refreshAcct();
      }
    } catch {}
  };

  useEffect(() => { checkSignal(); const t = setInterval(checkSignal, 3000); return () => clearInterval(t); }, []);
  useEffect(() => { if (!active) return; const t = setInterval(runAutoTrade, 2000); return () => clearInterval(t); }, [active]);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Sentiment */}
        <div className="bg-dark-800 border border-gray-700/50 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <div className="text-xs text-gray-500 uppercase tracking-wider">Market Sentiment</div>
            <button onClick={refreshSentiment} disabled={loading}
              className="text-xs text-accent hover:text-accent-hover disabled:opacity-50">
              {loading ? 'Loading...' : 'Refresh'}
            </button>
          </div>
          {sentiment ? (
            <div>
              <div className={`text-xl font-bold mb-2 ${
                sentiment.sentiment === 'BULLISH' ? 'text-green' :
                sentiment.sentiment === 'BEARISH' ? 'text-red' : 'text-gray-400'
              }`}>{sentiment.sentiment}</div>
              <div className="text-xs text-gray-500 max-h-32 overflow-y-auto whitespace-pre-wrap">{sentiment.headlines}</div>
            </div>
          ) : (
            <div className="text-gray-600 text-sm">Click Refresh to analyze news</div>
          )}
        </div>

        {/* SMA Signal */}
        <div className="bg-dark-800 border border-gray-700/50 rounded-xl p-5">
          <div className="text-xs text-gray-500 uppercase tracking-wider mb-3">SMA Crossover</div>
          {smaSignal?.signal ? (
            <div>
              <div className={`text-xl font-bold mb-2 ${smaSignal.signal === 'BUY' ? 'text-green' : 'text-red'}`}>
                {smaSignal.signal}
              </div>
              <div className="text-xs text-gray-400 font-mono">
                SMA({smaSignal.fast}) {smaSignal.fast > smaSignal.slow ? '>' : '<'} SMA({smaSignal.slow})
              </div>
            </div>
          ) : (
            <div className="text-gray-600 text-sm">
              {smaSignal ? `Collecting data (${smaSignal.data_points}/${smaSignal.needed} ticks)` : 'Loading...'}
            </div>
          )}
        </div>
      </div>

      {/* Auto-trade control */}
      <div className="bg-dark-800 border border-gray-700/50 rounded-xl p-5">
        <div className="flex items-center justify-between mb-3">
          <div className="text-xs text-gray-500 uppercase tracking-wider">Auto-Trade Engine</div>
          <button onClick={() => setActive(!active)}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              active ? 'bg-green text-white' : 'bg-dark-700 border border-gray-600 text-gray-400 hover:text-white'
            }`}>
            {active ? 'Running' : 'Paused'}
          </button>
        </div>
        <p className="text-xs text-gray-500 mb-3">
          Trades execute automatically when SMA + Sentiment align. Enable to start.
        </p>
        {active && smaSignal?.signal && sentiment?.sentiment && (
          <div className="text-xs text-gray-400 font-mono">
            SMA: {smaSignal.signal} · Sentiment: {sentiment.sentiment} ·
            {(smaSignal.signal === 'BUY' && sentiment.sentiment === 'BULLISH') ||
             (smaSignal.signal === 'SELL' && sentiment.sentiment === 'BEARISH')
              ? ' <span className="text-green">ALIGNED</span>'
              : ' Waiting for alignment'}
          </div>
        )}
      </div>

      {/* Auto trade log */}
      {autoLog.length > 0 && (
        <div className="bg-dark-800 border border-gray-700/50 rounded-xl p-5">
          <div className="text-xs text-gray-500 uppercase tracking-wider mb-3">Auto Trade Log</div>
          <div className="space-y-1 max-h-60 overflow-y-auto">
            {autoLog.map((entry, i) => (
              <div key={i} className="text-xs font-mono text-gray-400 py-1 border-b border-gray-800/50">{entry}</div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function Trading() {
  const [tab, setTab] = useState('manual');

  const tabs = [
    { id: 'manual', label: 'Manual' },
    { id: 'copilot', label: 'Co-Pilot' },
    { id: 'auto', label: 'Autonomous' },
  ];

  return (
    <div className="max-w-6xl mx-auto space-y-4">
      {/* Mobile desktop-mode hint */}
      <div className="md:hidden text-center text-xs text-gray-500 bg-dark-800 border border-gray-700/50 rounded-lg px-3 py-2">
        For the best experience, switch to desktop mode or use a computer
      </div>
      <h1 className="text-lg font-semibold text-white">Trading</h1>

      <div className="flex gap-1 bg-dark-800 rounded-xl p-1 w-fit">
        {tabs.map(({ id, label }) => (
          <button key={id} onClick={() => setTab(id)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              tab === id ? 'bg-accent text-white' : 'text-gray-400 hover:text-gray-200'
            }`}>
            {label}
          </button>
        ))}
      </div>

      {tab === 'manual' && <ManualTab />}
      {tab === 'copilot' && <CopilotTab />}
      {tab === 'auto' && <AutonomousTab />}
    </div>
  );
}
