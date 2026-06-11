import { useState } from 'react';
import { LayoutDashboard, TrendingUp, BarChart3, Briefcase, Settings, LogOut, Menu, X } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useSession } from '../App';

const items = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, path: '/dashboard' },
  { id: 'trading', label: 'Trading', icon: TrendingUp, path: '/trading' },
  { id: 'analytics', label: 'Analytics', icon: BarChart3, path: '/analytics' },
  { id: 'portfolio', label: 'Portfolio', icon: Briefcase, path: '/portfolio' },
  { id: 'settings', label: 'Settings', icon: Settings, path: '/settings' },
];

export default function Sidebar() {
  const { acct, logout } = useSession();
  const navigate = useNavigate();
  const location = useLocation();
  const current = location.pathname.replace('/', '') || 'dashboard';
  const [open, setOpen] = useState(false);

  const go = (path) => { navigate(path); setOpen(false); };

  return (
    <>
      {/* Mobile header */}
      <div className="md:hidden fixed top-0 left-0 right-0 h-12 bg-dark-800 border-b border-gray-600/50 flex items-center px-2 z-50 shadow-lg">
        <button onClick={() => setOpen(!open)} className="text-white hover:text-accent w-10 h-10 flex items-center justify-center rounded-lg hover:bg-dark-700 transition-colors">
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
        <div className="flex-1 text-center text-sm font-semibold text-white tracking-wide">AuraTrader AI</div>
        <button onClick={logout} className="flex items-center gap-1.5 text-gray-300 hover:text-red-400 text-sm font-medium px-3 py-1.5 rounded-lg hover:bg-dark-700 transition-colors border border-gray-600/30">
          <LogOut size={14} />
          Sign Out
        </button>
      </div>

      {/* Mobile overlay */}
      {open && <div className="md:hidden fixed inset-0 bg-black/60 z-40" onClick={() => setOpen(false)} />}

      {/* Mobile menu */}
      <div className={`md:hidden fixed top-12 left-0 right-0 bg-dark-800 border-b border-gray-700/50 z-50 transition-transform ${open ? 'translate-y-0' : '-translate-y-full'}`}>
        {acct && (
          <div className="px-4 py-3 border-b border-gray-700/50">
            <div className="text-xs text-gray-400">Balance <span className="text-gray-200 font-mono">${acct.balance?.toLocaleString()}</span></div>
          </div>
        )}
        <nav className="p-2">
          {items.map(({ id, label, icon: Icon, path }) => (
            <button key={id} onClick={() => go(path)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm transition-colors ${
                current === id ? 'bg-accent/10 text-accent' : 'text-gray-400 hover:text-gray-200 hover:bg-dark-700'
              }`}>
              <Icon size={16} />
              {label}
            </button>
          ))}
        </nav>
      </div>

      {/* Desktop sidebar */}
      <aside className="w-56 bg-dark-800 border-r border-gray-700/50 flex-col shrink-0 hidden md:flex">
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
            <button key={id} onClick={() => navigate(path)}
              className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors ${
                current === id ? 'bg-accent/10 text-accent' : 'text-gray-400 hover:text-gray-200 hover:bg-dark-700'
              }`}>
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
    </>
  );
}
