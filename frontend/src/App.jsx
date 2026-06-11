import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect, createContext, useContext, useCallback } from 'react';
import { api } from './api';
import Home from './pages/Home';
import Dashboard from './pages/Dashboard';
import Trading from './pages/Trading';
import Analytics from './pages/Analytics';
import Portfolio from './pages/Portfolio';
import Settings from './pages/Settings';
import Sidebar from './components/Sidebar';

const SessionCtx = createContext(null);

export function useSession() { return useContext(SessionCtx); }

export default function App() {
  const [sid, setSid] = useState(() => localStorage.getItem('sid'));
  const [acct, setAcct] = useState(null);
  const [prices, setPrices] = useState({});
  const [page, setPage] = useState('dashboard');

  const refreshAcct = useCallback(async () => {
    if (!sid) return;
    try { setAcct(await api.getAccount(sid)); } catch {}
  }, [sid]);

  useEffect(() => { refreshAcct(); const t = setInterval(refreshAcct, 3000); return () => clearInterval(t); }, [refreshAcct]);

  const createSession = async (balance) => {
    const { session_id } = await api.createSession(balance);
    localStorage.setItem('sid', session_id);
    setSid(session_id);
  };

  const logout = () => {
    if (sid) api.deleteSession(sid).catch(() => {});
    localStorage.removeItem('sid');
    setSid(null);
    setAcct(null);
  };

  if (!sid) return <Home onCreate={createSession} />;

  return (
    <SessionCtx.Provider value={{ sid, acct, prices, setPrices, refreshAcct, logout }}>
      <div className="flex h-screen overflow-hidden">
        <Sidebar page={page} setPage={setPage} />
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/trading" element={<Trading />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/portfolio" element={<Portfolio />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </SessionCtx.Provider>
  );
}
