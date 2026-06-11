import { useState, useEffect, useCallback } from 'react';
import { useSession } from '../App';
import { api } from '../api';

export default function Portfolio() {
  const { sid, acct, refreshAcct } = useSession();
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

  useEffect(() => { refresh(); const t = setInterval(refresh, 3000); return () => clearInterval(t); }, [refresh]);

  const handleClose = async (ticketId, price) => {
    await api.closePosition(sid, { ticket_id: ticketId, exit_price: price });
    refresh();
  };

  const totalRisk = positions.reduce((acc, pos) => {
    if (pos.stop_loss > 0) {
      return acc + Math.abs(pos.entry_price - pos.stop_loss) * 100000 * pos.volume_lots;
    }
    return acc;
  }, 0);

  const bal = acct?.balance || 0;
  const riskPct = bal > 0 ? (totalRisk / bal * 100) : 0;

  return (
    <div className="max-w-5xl mx-auto space-y-4">
      {/* Mobile desktop-mode hint */}
      <div className="md:hidden text-center text-xs text-gray-500 bg-dark-800 border border-gray-700/50 rounded-lg px-3 py-2">
        For the best experience, switch to desktop mode or use a computer
      </div>
      <h1 className="text-lg font-semibold text-white">Portfolio</h1>

      {/* Risk overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Balance', value: `$${bal.toLocaleString(undefined,{minimumFractionDigits:2})}` },
          { label: 'Equity', value: `$${(acct?.equity||0).toLocaleString(undefined,{minimumFractionDigits:2})}` },
          { label: 'Used Margin', value: `$${(acct?.used_margin||0).toFixed(2)}` },
          { label: 'Risk at Stake', value: `$${totalRisk.toFixed(2)}`, cls: totalRisk > 0 ? 'text-red' : '' },
        ].map(({ label, value, cls }) => (
          <div key={label} className="bg-dark-800 border border-gray-700/50 rounded-xl p-3">
            <div className="text-xs text-gray-500 mb-1">{label}</div>
            <div className={`text-lg font-semibold font-mono ${cls || 'text-white'}`}>{value}</div>
          </div>
        ))}
      </div>

      {/* Open positions */}
      <div className="bg-dark-800 border border-gray-700/50 rounded-xl p-4">
        <div className="text-xs text-gray-500 uppercase tracking-wider mb-3">Open Positions ({positions.length})</div>
        {positions.length === 0 ? (
          <div className="text-gray-600 text-sm">No open positions</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-gray-500 border-b border-gray-700/50">
                  <th className="text-left py-2 px-2">#</th>
                  <th className="text-left py-2 px-2">Instrument</th>
                  <th className="text-left py-2 px-2">Side</th>
                  <th className="text-right py-2 px-2">Lots</th>
                  <th className="text-right py-2 px-2">Entry</th>
                  <th className="text-right py-2 px-2">Current</th>
                  <th className="text-right py-2 px-2">SL</th>
                  <th className="text-right py-2 px-2">TP</th>
                  <th className="text-right py-2 px-2">Action</th>
                </tr>
              </thead>
              <tbody>
                {positions.map((pos) => (
                  <tr key={pos.ticket_id} className="border-b border-gray-800/50">
                    <td className="py-2 px-2 text-gray-400">{pos.ticket_id}</td>
                    <td className="py-2 px-2">{pos.instrument?.replace('_','/')}</td>
                    <td className={`py-2 px-2 font-medium ${pos.direction === 'BUY' ? 'text-green' : 'text-red'}`}>{pos.direction}</td>
                    <td className="py-2 px-2 text-right text-gray-300">{pos.volume_lots}</td>
                    <td className="py-2 px-2 text-right font-mono text-gray-300">{pos.entry_price?.toFixed(5)}</td>
                    <td className="py-2 px-2 text-right font-mono text-gray-300">{pos.current_price?.toFixed(5)}</td>
                    <td className="py-2 px-2 text-right font-mono text-gray-500">{pos.stop_loss > 0 ? pos.stop_loss.toFixed(5) : '—'}</td>
                    <td className="py-2 px-2 text-right font-mono text-gray-500">{pos.take_profit > 0 ? pos.take_profit.toFixed(5) : '—'}</td>
                    <td className="py-2 px-2 text-right">
                      <button onClick={() => handleClose(pos.ticket_id, pos.current_price)}
                        className="text-xs text-red hover:text-red-muted px-2 py-1 border border-red/30 rounded">
                        Close
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Trade history */}
      <div className="bg-dark-800 border border-gray-700/50 rounded-xl p-4">
        <div className="text-xs text-gray-500 uppercase tracking-wider mb-3">Trade History ({history.length})</div>
        {history.length === 0 ? (
          <div className="text-gray-600 text-sm">No closed trades yet</div>
        ) : (
          <div className="overflow-x-auto max-h-80 overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-dark-800">
                <tr className="text-xs text-gray-500 border-b border-gray-700/50">
                  <th className="text-left py-2 px-2">#</th>
                  <th className="text-left py-2 px-2">Instrument</th>
                  <th className="text-left py-2 px-2">Side</th>
                  <th className="text-right py-2 px-2">Entry</th>
                  <th className="text-right py-2 px-2">Exit</th>
                  <th className="text-right py-2 px-2">P&L</th>
                  <th className="text-left py-2 px-2">Reason</th>
                </tr>
              </thead>
              <tbody>
                {history.map((t, i) => (
                  <tr key={i} className="border-b border-gray-800/50">
                    <td className="py-2 px-2 text-gray-400">{t.ticket_id}</td>
                    <td className="py-2 px-2">{t.instrument?.replace('_','/')}</td>
                    <td className={`py-2 px-2 font-medium ${t.direction === 'BUY' ? 'text-green' : 'text-red'}`}>{t.direction}</td>
                    <td className="py-2 px-2 text-right font-mono text-gray-300">{t.entry_price?.toFixed(5)}</td>
                    <td className="py-2 px-2 text-right font-mono text-gray-300">{t.exit_price?.toFixed(5)}</td>
                    <td className={`py-2 px-2 text-right font-mono ${t.profit_loss >= 0 ? 'text-green' : 'text-red'}`}>
                      ${t.profit_loss?.toFixed(2)}
                    </td>
                    <td className="py-2 px-2 text-gray-400">{t.exit_reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
