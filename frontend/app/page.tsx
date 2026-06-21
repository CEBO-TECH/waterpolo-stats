'use client';

import { useEffect, useState, useCallback } from 'react';
import { api } from '@/lib/api';
import { AppState, ClubInfo, Mode, Settings } from '@/lib/types';
import { useOfflineQueue } from '@/lib/useOfflineQueue';
import LoginPage from '@/components/LoginPage';
import AppNav from '@/components/AppNav';
import Dashboard from '@/components/Dashboard';
import ScoreKeeper from '@/components/ScoreKeeper';
import StatsPanel from '@/components/StatsPanel';
import PlayersPanel from '@/components/PlayersPanel';
import MatchesPanel from '@/components/MatchesPanel';
import AdminPanel from '@/components/AdminPanel';
import UsersPanel from '@/components/UsersPanel';
import PlayerView from '@/components/PlayerView';
import MvpSummary from '@/components/MvpSummary';

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
    clubs: [],
    currentClubId: '',
    ageCategories: [],
    youtube: null,
  });

  const [mode, setMode] = useState<Mode>('dashboard');
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [navCollapsed, setNavCollapsed] = useState<boolean>(
    () => typeof window !== 'undefined' && localStorage.getItem('nav_collapsed') === '1',
  );

  const collapseNav = () => { setNavCollapsed(true); try { localStorage.setItem('nav_collapsed', '1'); } catch {} };
  const expandNav = () => { setNavCollapsed(false); setDrawerOpen(false); try { localStorage.removeItem('nav_collapsed'); } catch {} };
  const [attackMode, setAttackMode] = useState<'positional' | 'man_up'>('positional');
  const { connectionStatus, queuedRequests, manualSync } = useOfflineQueue();

  const [scorePopup, setScorePopup] = useState<{
    show: boolean; quarter: number; my: string; opp: string;
  }>({ show: false, quarter: 1, my: '', opp: '' });

  const [endMatchPopup, setEndMatchPopup] = useState(false);
  const [mvpSummary, setMvpSummary] = useState<{ matchId: string; data: any } | null>(null);

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

  // Accept a club invitation from ?invite=<token> once authenticated.
  useEffect(() => {
    if (authenticated !== true) return;
    const token = new URLSearchParams(window.location.search).get('invite');
    if (!token) return;
    (async () => {
      try {
        await api.acceptInvitation(token);
        showToast('Dołączono do klubu');
        bootstrap();
      } catch (e: any) {
        showToast(e.message || 'Nie udało się przyjąć zaproszenia');
      } finally {
        window.history.replaceState({}, '', window.location.pathname);
      }
    })();
  }, [authenticated]); // eslint-disable-line

  const bootstrap = async () => {
    setLoading(true);
    try {
      const data = await api.bootstrap();
      let clubs: ClubInfo[] = [];
      try {
        const me = await api.getMe();
        clubs = me.clubs || [];
      } catch {
        // non-fatal — club switcher just won't show
      }
      setState(prev => ({
        ...prev,
        settings: data.settings,
        players: data.players,
        matches: data.matches,
        user: data.user,
        rosterActive: data.rosterActive || [],
        config: data.config,
        clubs,
        currentClubId: api.getCurrentClubId(),
        ageCategories: data.ageCategories || [],
        youtube: data.youtube || null,
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
      clubs: [], currentClubId: '', ageCategories: [], youtube: null,
    });
  };

  const switchClub = async (clubId: string) => {
    if (!clubId || clubId === state.currentClubId) return;
    setLoading(true);
    try {
      await api.selectClub(clubId);
      setMode('score');
      setDrawerOpen(false);
      await bootstrap();
      showToast('Zmieniono klub');
    } catch (e: any) {
      showToast(e.message || 'Błąd zmiany klubu');
    } finally {
      setLoading(false);
    }
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
      // When queued offline the response has no Quarter — update it optimistically.
      setState(prev => ({
        ...prev,
        settings: settings?.queued
          ? { ...(prev.settings as Settings), Quarter: q }
          : settings,
      }));
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
      const mvp = await api.getMvp(matchId);
      if (mvp) setMvpSummary({ matchId, data: mvp });
    } catch (e: any) {
      showToast(e.message || 'Błąd');
    }
  };

  const confirmMvp = async (playerId: string) => {
    if (!mvpSummary) return;
    try {
      await api.confirmMvp(mvpSummary.matchId, playerId);
      showToast('Zapisano MVP');
    } catch (e: any) {
      showToast(e.message || 'Błąd');
    } finally {
      setMvpSummary(null);
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

  // Close drawer with Escape
  useEffect(() => {
    if (!drawerOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setDrawerOpen(false);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [drawerOpen]);

  const selectMode = (m: Mode) => {
    setMode(m);
    setDrawerOpen(false);
  };

  // ─── Auth loading ───
  if (authenticated === null) {
    return <div className="loading-overlay"><div className="spinner" /></div>;
  }
  if (authenticated === false) {
    return <LoginPage onLogin={onLogin} />;
  }

  // Players get a restricted, self-service view (their stats + their matches).
  if (state.user?.role === 'player') {
    return <PlayerView state={state} onLogout={logout} />;
  }

  return (
    <div className={`app-shell${navCollapsed ? ' nav-collapsed' : ''}`}>
      <AppNav
        mode={mode}
        onSelect={selectMode}
        variant="sidebar"
        user={state.user}
        onLogout={logout}
        clubs={state.clubs}
        currentClubId={state.currentClubId}
        onSwitchClub={switchClub}
        onCollapse={collapseNav}
      />

      <div className="app-main">
      <header>
        <button
          className="burger"
          onClick={() => setDrawerOpen(true)}
          aria-label="Otwórz menu"
        >
          ☰
        </button>

        {mode === 'score' && (
          <>
            <div className="tag">
              Mecz:
              <select
                value={state.settings?.ActiveMatch || ''}
                onChange={e => setMatch(e.target.value)}
              >
                {state.matches.map(m => (
                  <option key={m.match_id} value={m.match_id}>
                    vs {m.opponent || m.match_id} ({m.ageCategory || 'bez kat.'})
                  </option>
                ))}
              </select>
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
      </header>

      {drawerOpen && (
        <>
          <div className="drawer-overlay" onClick={() => setDrawerOpen(false)} />
          <div className="drawer">
            <AppNav
              mode={mode}
              onSelect={selectMode}
              variant="drawer"
              user={state.user}
              onLogout={logout}
              onClose={() => setDrawerOpen(false)}
              clubs={state.clubs}
              currentClubId={state.currentClubId}
              onSwitchClub={switchClub}
              onPin={navCollapsed ? expandNav : undefined}
            />
          </div>
        </>
      )}

      {mode === 'dashboard' && (
        <Dashboard
          state={state}
          showToast={showToast}
          goToMode={(m) => setMode(m)}
          setMatch={setMatch}
        />
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
        />
      )}
      {mode === 'stats' && <StatsPanel state={state} showToast={showToast} />}
      {mode === 'players' && <PlayersPanel state={state} showToast={showToast} refresh={bootstrap} />}
      {mode === 'matches' && <MatchesPanel state={state} showToast={showToast} refresh={bootstrap} />}
      {mode === 'admin' && <AdminPanel state={state} showToast={showToast} refresh={bootstrap} />}
      {mode === 'users' && <UsersPanel state={state} showToast={showToast} />}

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

      {mvpSummary && (
        <MvpSummary
          data={mvpSummary.data}
          onConfirm={confirmMvp}
          onClose={() => setMvpSummary(null)}
        />
      )}
      </div>
    </div>
  );
}
