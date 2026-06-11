import { useState, useEffect } from 'react';
import { useSession } from '../App';
import { api } from '../api';

export default function Analytics() {
  const { sid } = useSession();
  const [metrics, setMetrics] = useState({});
  const [history, setHistory] = useState([]);

  useEffect(() => {
    (async () => {
      try {
        const [m, h] = await Promise.all([api.getMetrics(sid), api.getHistory(sid)]);
        setMetrics(m);
        setHistory(h);
      } catch {}
    })();
  }, [sid]);

  const stat = (label, value, cls = '') => (
    <div className="bg-dark-800 border border-gray-700/50 rounded-xl p-4">
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className={`text-lg font-semibold font-mono ${cls}`}>{value}</div>
    </div>
  );

  return (
    <div className="max-w-5xl mx-auto space-y-4">
      <h1 className="text-lg font-semibold text-white">Analytics</h1>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {stat('Total P&L', `$${(metrics.total_pnl||0).toFixed(2)}`, metrics.total_pnl >= 0 ? 'text-green' : 'text-red')}
        {stat('Win Rate', `${(metrics.win_rate||0).toFixed(1)}%`, metrics.win_rate >= 50 ? 'text-green' : 'text-red')}
        {stat('Total Trades', metrics.total_trades || 0)}
        {stat('Max Drawdown', `${(metrics.max_drawdown||0).toFixed(2)}%`, 'text-red')}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {stat('Best Trade', `$${(metrics.best_trade||0).toFixed(2)}`, 'text-green')}
        {stat('Worst Trade', `$${(metrics.worst_trade||0).toFixed(2)}`, 'text-red')}
        {stat('Avg Win', `$${(metrics.avg_win||0).toFixed(2)}`, 'text-green')}
        {stat('Avg Loss', `$${(metrics.avg_loss||0).toFixed(2)}`, 'text-red')}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {stat('Sharpe Ratio', metrics.sharpe || 0)}
        {stat('Sortino Ratio', metrics.sortino || 0)}
        {stat('Open Positions', metrics.open_positions || 0)}
      </div>

      {/* Trade history table */}
      <div className="bg-dark-800 border border-gray-700/50 rounded-xl p-4">
        <div className="text-xs text-gray-500 uppercase tracking-wider mb-3">Trade History</div>
        {history.length === 0 ? (
          <div className="text-gray-600 text-sm">No trades yet</div>
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
                    <td className="py-2 px-2 text-right text-gray-300">{t.volume_lots}</td>
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
