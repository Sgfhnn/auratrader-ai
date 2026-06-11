import { LayoutDashboard, TrendingUp, BarChart3, Briefcase, Settings, LogOut } from 'lucide-react';

const items = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, path: '/dashboard' },
  { id: 'trading', label: 'Trading', icon: TrendingUp, path: '/trading' },
  { id: 'analytics', label: 'Analytics', icon: BarChart3, path: '/analytics' },
  { id: 'portfolio', label: 'Portfolio', icon: Briefcase, path: '/portfolio' },
  { id: 'settings', label: 'Settings', icon: Settings, path: '/settings' },
];

export default function Sidebar({ page, setPage }) {
  const { acct, logout } = require('../App').useSession();

  return (
    <aside className="w-56 bg-dark-800 border-r border-gray-700/50 flex flex-col shrink-0 hidden md:flex">
      <div className="p-4 border-b border-gray-700/50">
        <div className="text-sm font-semibold text-accent tracking-wide">AuraTrader AI</div>
        {acct && (
          <div className="mt-2 text-xs text-gray-400">
            Balance <span className="text-gray-200 font-mono">${acct.balance?.toLocaleString()}</span>
          </div>
        )}
      </div>
      <nav className="flex-1 p-2 space-y-0.5">
        {items.map(({ id, label, icon: Icon, path }) => (
          <button
            key={id}
            onClick={() => { setPage(id); window.history.pushState(null, '', path); }}
            className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors ${
              page === id ? 'bg-accent/10 text-accent' : 'text-gray-400 hover:text-gray-200 hover:bg-dark-700'
            }`}
          >
            <Icon size={16} />
            {label}
          </button>
        ))}
      </nav>
      <div className="p-2 border-t border-gray-700/50">
        <button onClick={logout} className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-gray-400 hover:text-red-400 hover:bg-dark-700 transition-colors">
          <LogOut size={16} />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
