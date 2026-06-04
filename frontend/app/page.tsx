'use client';

import { useEffect, useState, useCallback } from 'react';
import { api } from '@/lib/api';
import { AppState, Mode } from '@/lib/types';
import { useOfflineQueue } from '@/lib/useOfflineQueue';
import LoginPage from '@/components/LoginPage';
import ScoreKeeper from '@/components/ScoreKeeper';
import StatsPanel from '@/components/StatsPanel';
import PlayersPanel from '@/components/PlayersPanel';
import MatchesPanel from '@/components/MatchesPanel';
import AdminPanel from '@/components/AdminPanel';

export default function Home() {
  const [authenticated, setAuthenticated] = useState<boolean | null>(null);
  const [state, setState] = useState<AppState>({
    settings: null,
    players: [],
    matches: [],
    selected: null,
    stats: null,
    user: null,
    rosterActive: [],
    recentEvents: [],
    config: null,
  });

  const [mode, setMode] = useState<Mode>('score');
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [attackMode, setAttackMode] = useState<'positional' | 'man_up'>('positional');
  const [note, setNote] = useState('');
  const { connectionStatus, queuedRequests, manualSync } = useOfflineQueue();

  const [scorePopup, setScorePopup] = useState<{
    show: boolean; quarter: number; my: string; opp: string;
  }>({ show: false, quarter: 1, my: '', opp: '' });

  const [endMatchPopup, setEndMatchPopup] = useState(false);

  const showToast = useCallback((msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 1400);
  }, []);

  useEffect(() => {
    if (api.isAuthenticated()) {
      setAuthenticated(true);
      bootstrap();
    } else {
      setAuthenticated(false);
    }
  }, []); // eslint-disable-line

  const bootstrap = async () => {
    setLoading(true);
    try {
      const data = await api.bootstrap();
      setState(prev => ({
        ...prev,
        settings: data.settings,
        players: data.players,
        matches: data.matches,
        user: data.user,
        rosterActive: data.rosterActive || [],
        config: data.config,
      }));
    } catch (e: any) {
      if (e.message?.includes('authenticated') || e.message?.includes('Bootstrap')) {
        setAuthenticated(false);
      }
    } finally {
      setLoading(false);
    }
  };

  const onLogin = () => {
    setAuthenticated(true);
    bootstrap();
  };

  const logout = () => {
    api.logout();
    setAuthenticated(false);
    setState({
      settings: null, players: [], matches: [], selected: null,
      stats: null, user: null, rosterActive: [], recentEvents: [], config: null,
    });
  };

  const setMatch = async (matchId: string) => {
    try {
      const settings = await api.setActiveMatch(matchId);
      const roster = await api.getRoster(matchId);
      setState(prev => ({
        ...prev,
        settings,
        rosterActive: roster,
        selected: null,
        recentEvents: [],
      }));
      loadRecentEvents(matchId);
    } catch (e: any) {
      showToast(e.message || 'Błąd');
    }
  };

  const setQuarter = async (q: number) => {
    const currentQ = state.settings?.Quarter || 1;
    if (q > currentQ) {
      setScorePopup({ show: true, quarter: currentQ, my: '', opp: '' });
    }
    try {
      const settings = await api.setQuarter(q);
      setState(prev => ({ ...prev, settings }));
    } catch (e: any) {
      showToast(e.message || 'Błąd');
    }
  };

  const saveScore = async () => {
    const matchId = state.settings?.ActiveMatch;
    if (!matchId) return;
    try {
      await api.updateScore(
        matchId,
        String(scorePopup.quarter),
        Number(scorePopup.my) || 0,
        Number(scorePopup.opp) || 0,
      );
      setScorePopup({ show: false, quarter: 1, my: '', opp: '' });
      showToast('Wynik zapisany');
    } catch (e: any) {
      showToast(e.message || 'Błąd');
    }
  };

  const endMatch = async () => {
    const matchId = state.settings?.ActiveMatch;
    if (!matchId) return;
    try {
      await api.endMatch(matchId);
      setEndMatchPopup(false);
      showToast('Mecz zakończony');
      bootstrap();
    } catch (e: any) {
      showToast(e.message || 'Błąd');
    }
  };

  const loadRecentEvents = async (matchId?: string) => {
    const mid = matchId || state.settings?.ActiveMatch;
    if (!mid) return;
    try {
      const events = await api.getEvents(mid);
      setState(prev => ({ ...prev, recentEvents: events }));
    } catch (e) {
      // silent
    }
  };

  const isMatchActive = () => {
    const m = state.matches.find(m => m.match_id === state.settings?.ActiveMatch);
    return m?.status === 'active';
  };

  useEffect(() => {
    if (mode === 'score' && state.settings?.ActiveMatch) {
      loadRecentEvents();
    }
  }, [mode, state.settings?.ActiveMatch]); // eslint-disable-line

  // ─── Auth loading ───
  if (authenticated === null) {
    return <div className="loading-overlay"><div className="spinner" /></div>;
  }
  if (authenticated === false) {
    return <LoginPage onLogin={onLogin} />;
  }

  const MODES: { key: Mode; label: string }[] = [
    { key: 'score', label: 'Asystent' },
    { key: 'stats', label: 'Statystyki' },
    { key: 'players', label: 'Zawodnicy' },
    { key: 'matches', label: 'Mecze' },
    { key: 'admin', label: 'Nowy mecz' },
  ];

  return (
    <>
      <header>
        <div className="tag">
          Mecz:
          <select
            value={state.settings?.ActiveMatch || ''}
            onChange={e => setMatch(e.target.value)}
          >
            {state.matches.map(m => (
              <option key={m.match_id} value={m.match_id}>
                vs {m.opponent || m.match_id} ({m.ageCategory})
              </option>
            ))}
          </select>
        </div>

        {mode === 'score' && (
          <>
            <div className="tag">
              Q: <span style={{ color: 'var(--accent)', fontWeight: 700 }}>
                {state.settings?.Quarter || 1}
              </span>
            </div>
            {[1, 2, 3, 4].map(q => (
              <button
                key={q}
                className={`qbtn${state.settings?.Quarter === q ? ' selected' : ''}`}
                onClick={() => setQuarter(q)}
                disabled={!isMatchActive()}
              >
                Q{q}
              </button>
            ))}
            {isMatchActive() && (
              <button className="btn primary" onClick={() => setEndMatchPopup(true)} style={{ marginLeft: 8 }}>
                Zakończ mecz
              </button>
            )}
            {!isMatchActive() && state.settings?.ActiveMatch && (
              <div className="tag" style={{ borderColor: 'var(--orange)', color: 'var(--orange)' }}>
                Mecz zakończony
              </div>
            )}
          </>
        )}

        <div style={{ marginLeft: 'auto' }} />

        {MODES.map(m => (
          <button
            key={m.key}
            className={`btn small${mode === m.key ? ' primary' : ''}`}
            onClick={() => { setMode(m.key); setDrawerOpen(false); }}
          >
            {m.label}
          </button>
        ))}

        {/* Connection status */}
        <div className="tag" style={{
          borderColor: connectionStatus === 'online' ? 'var(--green)' : 'var(--red)',
        }}>
          <div className={`status-dot ${connectionStatus}`} />
          <span className="small">
            {connectionStatus === 'online' ? 'Online' : 'Offline'}
            {queuedRequests > 0 && ` (${queuedRequests})`}
          </span>
          {queuedRequests > 0 && connectionStatus === 'online' && (
            <button className="btn small" onClick={manualSync} style={{ padding: '2px 6px', minHeight: 20, fontSize: 10 }}>
              Sync
            </button>
          )}
        </div>

        {connectionStatus === 'offline' && (
          <div className="tag" style={{ borderColor: 'var(--orange)', color: 'var(--orange)' }}>
            Nie odswiezaj strony!
          </div>
        )}

        <div className="tag">
          <span className="small">{state.user?.email?.split('@')[0]}</span>
          <button className="btn small danger" onClick={logout} style={{ padding: '2px 8px', minHeight: 24 }}>
            Wyloguj
          </button>
        </div>

        <button onClick={() => setDrawerOpen(true)} style={{ display: 'none' }}>☰</button>
      </header>

      {drawerOpen && (
        <>
          <div className="drawer-overlay" onClick={() => setDrawerOpen(false)} />
          <div className="drawer">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div className="muted">Menu</div>
              <button onClick={() => setDrawerOpen(false)}>✕</button>
            </div>
            {MODES.map(m => (
              <button
                key={m.key}
                className={`btn menu-btn${mode === m.key ? ' primary' : ''}`}
                onClick={() => { setMode(m.key); setDrawerOpen(false); }}
              >
                {m.label}
              </button>
            ))}
            <div style={{ marginTop: 'auto', textAlign: 'center' }}>
              <div className="muted small">Powered by CEBO.TECH</div>
            </div>
          </div>
        </>
      )}

      {mode === 'score' && (
        <ScoreKeeper
          state={state}
          setState={setState}
          attackMode={attackMode}
          setAttackMode={setAttackMode}
          showToast={showToast}
          refreshEvents={() => loadRecentEvents()}
          refreshStats={() => {}}
          note={note}
          setNote={setNote}
        />
      )}
      {mode === 'stats' && <StatsPanel state={state} showToast={showToast} />}
      {mode === 'players' && <PlayersPanel state={state} showToast={showToast} refresh={bootstrap} />}
      {mode === 'matches' && <MatchesPanel state={state} showToast={showToast} refresh={bootstrap} />}
      {mode === 'admin' && <AdminPanel state={state} showToast={showToast} refresh={bootstrap} />}

      {loading && <div className="loading-overlay"><div className="spinner" /></div>}
      {toast && <div className="toast">{toast}</div>}

      {scorePopup.show && (
        <div className="popup-overlay" onClick={() => setScorePopup({ ...scorePopup, show: false })}>
          <div className="popup" onClick={e => e.stopPropagation()}>
            <h3>Wynik po Q{scorePopup.quarter}</h3>
            <div className="form-row" style={{ marginBottom: 16 }}>
              <div>
                <label>My</label>
                <input
                  type="number"
                  value={scorePopup.my}
                  onChange={e => setScorePopup({ ...scorePopup, my: e.target.value })}
                  autoFocus
                />
              </div>
              <div>
                <label>Przeciwnik</label>
                <input
                  type="number"
                  value={scorePopup.opp}
                  onChange={e => setScorePopup({ ...scorePopup, opp: e.target.value })}
                />
              </div>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn primary" onClick={saveScore}>Zapisz</button>
              <button className="btn" onClick={() => setScorePopup({ ...scorePopup, show: false })}>Pomiń</button>
            </div>
          </div>
        </div>
      )}

      {endMatchPopup && (
        <div className="popup-overlay" onClick={() => setEndMatchPopup(false)}>
          <div className="popup" onClick={e => e.stopPropagation()}>
            <h3>Zakończyć mecz?</h3>
            <p className="muted" style={{ marginBottom: 16 }}>
              Po zakończeniu nie będzie można dodawać ani edytować akcji.
            </p>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn danger" onClick={endMatch}>Zakończ mecz</button>
              <button className="btn" onClick={() => setEndMatchPopup(false)}>Anuluj</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
