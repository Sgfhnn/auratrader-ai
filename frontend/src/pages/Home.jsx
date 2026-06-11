import { useState } from 'react';

const presets = [
  { value: 1000, label: '$1K' },
  { value: 10000, label: '$10K' },
  { value: 50000, label: '$50K' },
  { value: 100000, label: '$100K' },
  { value: 1000000, label: '$1M' },
];

export default function Home({ onCreate }) {
  const [balance, setBalance] = useState(10000);
  const [loading, setLoading] = useState(false);

  const handleCreate = async () => {
    setLoading(true);
    await onCreate(balance);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-dark-900 px-4">
      <div className="max-w-md w-full text-center">
        <div className="text-xs font-medium text-accent tracking-[0.15em] uppercase mb-3">Trading Platform</div>
        <h1 className="text-3xl font-bold text-white tracking-tight">AuraTrader AI</h1>
        <div className="w-8 h-0.5 bg-accent mx-auto my-4 rounded-full" />
        <p className="text-sm text-gray-400 mb-8 leading-relaxed">
          AI-driven forex simulation with real-time matching engine.
        </p>

        <div className="text-xs text-gray-500 uppercase tracking-wider mb-3">Initial Capital</div>

        <div className="flex gap-2 justify-center mb-4">
          {presets.map(({ value, label }) => (
            <button
              key={value}
              onClick={() => setBalance(value)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                balance === value
                  ? 'bg-accent text-white'
                  : 'bg-dark-700 text-gray-400 hover:text-gray-200 border border-gray-700'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        <input
          type="number"
          value={balance}
          onChange={(e) => setBalance(Number(e.target.value))}
          min={1000}
          max={1000000}
          step={1000}
          className="w-full bg-dark-700 border border-gray-700 rounded-lg px-4 py-2.5 text-center text-lg font-mono text-white focus:outline-none focus:border-accent mb-4"
        />

        <div className="text-2xl font-bold font-mono text-white mb-6">
          ${balance.toLocaleString()}
        </div>

        <button
          onClick={handleCreate}
          disabled={loading}
          className="w-full py-3 bg-accent hover:bg-accent-hover text-white font-semibold rounded-lg transition-colors disabled:opacity-50"
        >
          {loading ? 'Starting...' : 'Start Simulation'}
        </button>
      </div>
    </div>
  );
}
