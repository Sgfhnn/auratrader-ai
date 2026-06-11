import { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
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

  // Chart data
  const sortedHistory = [...history].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
  const pnlBarData = sortedHistory.map((t, i) => ({ name: `#${i + 1}`, pnl: t.profit_loss }));
  const cumPnlData = sortedHistory.reduce((acc, t, i) => {
    const prev = acc.length > 0 ? acc[acc.length - 1].pnl : 0;
    acc.push({ name: `#${i + 1}`, pnl: prev + t.profit_loss });
    return acc;
  }, []);

  const wins = history.filter(t => t.profit_loss > 0).length;
  const losses = history.filter(t => t.profit_loss <= 0).length;
  const pieData = [
    { name: 'Wins', value: wins },
    { name: 'Losses', value: losses },
  ].filter(d => d.value > 0);

  return (
    <div className="max-w-6xl mx-auto space-y-4">
      <h1 className="text-lg font-semibold text-white">Analytics</h1>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {stat('Total P&L', `$${(metrics.total_pnl||0).toFixed(2)}`, metrics.total_pnl >= 0 ? 'text-green' : 'text-red')}
        {stat('Win Rate', `${(metrics.win_rate||0).toFixed(1)}%`, metrics.win_rate >= 50 ? 'text-green' : 'text-red')}
        {stat('Total Trades', metrics.total_trades || 0)}
        {stat('Max Drawdown', `${(metrics.max_drawdown||0).toFixed(2)}%`, 'text-red')}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {stat('Sharpe', metrics.sharpe || 0)}
        {stat('Sortino', metrics.sortino || 0)}
        {stat('Best Trade', `$${(metrics.best_trade||0).toFixed(2)}`, 'text-green')}
        {stat('Worst Trade', `$${(metrics.worst_trade||0).toFixed(2)}`, 'text-red')}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* P&L Bar Chart */}
        <div className="bg-dark-800 border border-gray-700/50 rounded-xl p-4">
          <div className="text-xs text-gray-500 uppercase tracking-wider mb-3">P&L per Trade</div>
          {pnlBarData.length === 0 ? (
            <div className="h-48 flex items-center justify-center text-gray-600 text-sm">No trades yet</div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={pnlBarData}>
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#475569' }} />
                <YAxis tick={{ fontSize: 10, fill: '#475569' }} />
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, fontSize: 12 }} />
                <Bar dataKey="pnl" fill="#3b82f6" radius={[4, 4, 0, 0]}>
                  {pnlBarData.map((entry, i) => (
                    <Cell key={i} fill={entry.pnl >= 0 ? '#22c55e' : '#ef4444'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Cumulative P&L */}
        <div className="bg-dark-800 border border-gray-700/50 rounded-xl p-4">
          <div className="text-xs text-gray-500 uppercase tracking-wider mb-3">Cumulative P&L</div>
          {cumPnlData.length === 0 ? (
            <div className="h-48 flex items-center justify-center text-gray-600 text-sm">No trades yet</div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={cumPnlData}>
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#475569' }} />
                <YAxis tick={{ fontSize: 10, fill: '#475569' }} />
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, fontSize: 12 }} />
                <Line type="monotone" dataKey="pnl" stroke="#22c55e" dot={false} strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Win/Loss + History */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Win/Loss pie */}
        <div className="bg-dark-800 border border-gray-700/50 rounded-xl p-4">
          <div className="text-xs text-gray-500 uppercase tracking-wider mb-3">Win / Loss</div>
          {pieData.length === 0 ? (
            <div className="h-40 flex items-center justify-center text-gray-600 text-sm">No data</div>
          ) : (
            <ResponsiveContainer width="100%" height={160}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={40} outerRadius={60} dataKey="value">
                  <Cell fill="#22c55e" />
                  <Cell fill="#ef4444" />
                </Pie>
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          )}
          <div className="flex justify-center gap-4 text-xs">
            <span className="text-green">Wins: {wins}</span>
            <span className="text-red">Losses: {losses}</span>
          </div>
        </div>

        {/* History table */}
        <div className="lg:col-span-2 bg-dark-800 border border-gray-700/50 rounded-xl p-4">
          <div className="text-xs text-gray-500 uppercase tracking-wider mb-3">Trade History</div>
          {history.length === 0 ? (
            <div className="text-gray-600 text-sm">No trades yet</div>
          ) : (
            <div className="overflow-x-auto max-h-64 overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-dark-800">
                  <tr className="text-xs text-gray-500 border-b border-gray-700/50">
                    <th className="text-left py-2 px-2">#</th>
                    <th className="text-left py-2 px-2">Pair</th>
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
    </div>
  );
}
