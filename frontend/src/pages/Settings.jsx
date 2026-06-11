import { useState, useEffect } from 'react';
import { useSession } from '../App';
import { api } from '../api';

export default function Settings() {
  const { sid, acct, logout } = useSession();
  const [config, setConfig] = useState({});
  const [dataSource, setDataSource] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const [c, ds] = await Promise.all([api.getConfig(), api.getDataSource()]);
        setConfig(c);
        setDataSource(ds.source);
      } catch {}
    })();
  }, []);

  const params = [
    ['Starting Balance', `$${(config.starting_balance||0).toLocaleString()}`],
    ['Spread', `${config.spread_pips} pips`],
    ['Max Slippage', `${config.max_slippage_pips} pips`],
    ['Margin Rate', `${((config.margin_rate||0)*100).toFixed(0)}%`],
    ['Lot Size', `${(config.lot_size||0).toLocaleString()} units`],
    ['Pip Size', config.pip_size],
    ['Tick Interval', `${config.tick_interval}s`],
    ['SMA Fast', `${config.sma_fast} ticks`],
    ['SMA Slow', `${config.sma_slow} ticks`],
    ['Auto SL', `${config.auto_sl_pips} pips`],
    ['Auto TP', `${config.auto_tp_pips} pips`],
  ];

  return (
    <div className="max-w-3xl mx-auto space-y-4">
      <h1 className="text-lg font-semibold text-white">Settings</h1>

      {/* Account */}
      <div className="bg-dark-800 border border-gray-700/50 rounded-xl p-5">
        <div className="text-xs text-gray-500 uppercase tracking-wider mb-4">Virtual Account</div>
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div>
            <div className="text-xs text-gray-500">Account ID</div>
            <div className="text-sm font-mono text-accent">#{acct?.account_id || 1}</div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Initial Balance</div>
            <div className="text-sm font-mono text-white">${(config.starting_balance||0).toLocaleString()}</div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Current Balance</div>
            <div className="text-sm font-mono text-white">${(acct?.balance||0).toLocaleString(undefined,{minimumFractionDigits:2})}</div>
          </div>
        </div>
        <button onClick={logout}
          className="px-4 py-2 bg-red/10 border border-red/30 text-red text-sm font-medium rounded-lg hover:bg-red/20 transition-colors">
          Reset Account
        </button>
      </div>

      {/* Data source */}
      <div className="bg-dark-800 border border-gray-700/50 rounded-xl p-5">
        <div className="text-xs text-gray-500 uppercase tracking-wider mb-3">Data Source</div>
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm text-white">{dataSource || 'Mock'}</div>
          </div>
          <span className="text-xs bg-accent/10 text-accent px-2 py-1 rounded-full">AUTO</span>
        </div>
      </div>

      {/* Trading parameters */}
      <div className="bg-dark-800 border border-gray-700/50 rounded-xl p-5">
        <div className="text-xs text-gray-500 uppercase tracking-wider mb-4">Trading Parameters</div>
        <div className="space-y-2">
          {params.map(([label, value]) => (
            <div key={label} className="flex items-center justify-between py-2 border-b border-gray-700/30 last:border-0">
              <div className="text-sm text-gray-300">{label}</div>
              <div className="text-sm font-mono text-accent">{value}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
