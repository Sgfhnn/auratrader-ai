import { useState, useEffect } from 'react';
import { useSession } from '../App';
import { api } from '../api';

const instruments = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'AUD_USD', 'USD_CAD'];

export default function Trading() {
  const { sid, prices, refreshAcct } = useSession();
  const [instrument, setInstrument] = useState('EUR_USD');
  const [direction, setDirection] = useState('BUY');
  const [volume, setVolume] = useState(0.1);
  const [sl, setSl] = useState(0);
  const [tp, setTp] = useState(0);
  const [loading, setLoading] = useState(false);
  const [lastTrade, setLastTrade] = useState(null);
  const [positions, setPositions] = useState([]);

  useEffect(() => {
    api.getPositions(sid).then(setPositions).catch(() => {});
  }, [sid]);

  const handleTrade = async () => {
    setLoading(true);
    try {
      const result = await api.openPosition(sid, { instrument, direction, volume_lots: volume, stop_loss: sl, take_profit: tp });
      setLastTrade(result);
      const pos = await api.getPositions(sid);
      setPositions(pos);
      refreshAcct();
    } catch {}
    setLoading(false);
  };

  const handleClose = async (ticketId, currentPrice) => {
    setLoading(true);
    try {
      await api.closePosition(sid, { ticket_id: ticketId, exit_price: currentPrice });
      setPositions(await api.getPositions(sid));
      refreshAcct();
    } catch {}
    setLoading(false);
  };

  const handleCloseAll = async () => {
    setLoading(true);
    try {
      await api.closeAll(sid, instrument);
      setPositions(await api.getPositions(sid));
      refreshAcct();
    } catch {}
    setLoading(false);
  };

  const p = prices[instrument] || {};
  const instPositions = positions.filter((pos) => pos.instrument === instrument);

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      <h1 className="text-lg font-semibold text-white">Trading</h1>

      {/* Order form */}
      <div className="bg-dark-800 border border-gray-700/50 rounded-xl p-5">
        <div className="text-xs text-gray-500 uppercase tracking-wider mb-4">New Order</div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Instrument</label>
            <select value={instrument} onChange={(e) => setInstrument(e.target.value)}
              className="w-full bg-dark-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-accent">
              {instruments.map((i) => <option key={i} value={i}>{i.replace('_','/')}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Volume (lots)</label>
            <input type="number" value={volume} onChange={(e) => setVolume(Number(e.target.value))}
              min={0.01} max={100} step={0.01}
              className="w-full bg-dark-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-accent" />
          </div>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Stop Loss</label>
            <input type="number" value={sl} onChange={(e) => setSl(Number(e.target.value))}
              step={0.0001}
              className="w-full bg-dark-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-accent" />
          </div>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Take Profit</label>
            <input type="number" value={tp} onChange={(e) => setTp(Number(e.target.value))}
              step={0.0001}
              className="w-full bg-dark-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-accent" />
          </div>
        </div>

        <div className="flex gap-3">
          <button onClick={() => { setDirection('BUY'); handleTrade(); }} disabled={loading}
            className="flex-1 py-2.5 bg-green hover:bg-green-muted text-white font-semibold rounded-lg disabled:opacity-50">
            BUY {p.ask?.toFixed(5) || ''}
          </button>
          <button onClick={() => { setDirection('SELL'); handleTrade(); }} disabled={loading}
            className="flex-1 py-2.5 bg-red hover:bg-red-muted text-white font-semibold rounded-lg disabled:opacity-50">
            SELL {p.bid?.toFixed(5) || ''}
          </button>
        </div>

        {lastTrade && (
          <div className="mt-3 text-xs text-green bg-green/10 border border-green/20 rounded-lg px-3 py-2">
            #{lastTrade.ticket_id} opened @ {lastTrade.entry_price?.toFixed(5)}
          </div>
        )}
      </div>

      {/* Open positions for this instrument */}
      <div className="bg-dark-800 border border-gray-700/50 rounded-xl p-5">
        <div className="flex items-center justify-between mb-3">
          <div className="text-xs text-gray-500 uppercase tracking-wider">
            Positions — {instrument.replace('_','/')}
          </div>
          {instPositions.length > 0 && (
            <button onClick={handleCloseAll} disabled={loading}
              className="text-xs text-red hover:text-red-muted disabled:opacity-50">
              Close All
            </button>
          )}
        </div>
        {instPositions.length === 0 ? (
          <div className="text-gray-600 text-sm">No open positions for this instrument</div>
        ) : (
          <div className="space-y-2">
            {instPositions.map((pos) => (
              <div key={pos.ticket_id} className="flex items-center justify-between bg-dark-700 rounded-lg px-4 py-2.5">
                <div className="flex items-center gap-4">
                  <span className={`text-xs font-bold ${pos.direction === 'BUY' ? 'text-green' : 'text-red'}`}>{pos.direction}</span>
                  <span className="text-sm text-gray-200">{pos.volume_lots} lots</span>
                  <span className="text-xs text-gray-400 font-mono">Entry {pos.entry_price?.toFixed(5)}</span>
                  <span className="text-xs text-gray-400 font-mono">Current {pos.current_price?.toFixed(5)}</span>
                  {pos.stop_loss > 0 && <span className="text-xs text-gray-500">SL {pos.stop_loss.toFixed(5)}</span>}
                  {pos.take_profit > 0 && <span className="text-xs text-gray-500">TP {pos.take_profit.toFixed(5)}</span>}
                </div>
                <button onClick={() => handleClose(pos.ticket_id, pos.current_price)} disabled={loading}
                  className="text-xs text-red hover:text-red-muted px-3 py-1 border border-red/30 rounded-lg disabled:opacity-50">
                  Close
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
