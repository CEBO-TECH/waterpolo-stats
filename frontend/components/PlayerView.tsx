'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { AppState } from '@/lib/types';

const RESULT: Record<string, { label: string; color: string }> = {
  W: { label: 'Z', color: 'var(--green)' },
  L: { label: 'P', color: 'var(--red)' },
  D: { label: 'R', color: 'var(--yellow)' },
};
const pct = (v: number) => `${Math.round((v || 0) * 100)}%`;

type Props = { state: AppState; onLogout: () => void };

export default function PlayerView({ state, onLogout }: Props) {
  const [player, setPlayer] = useState<any>(null);
  const [profile, setProfile] = useState<any>(null);
  const [matches, setMatches] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const clubName = state.clubs.find(c => c.club_id === state.currentClubId)?.club_name || '';

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const mp = await api.getMyPlayer();
        setPlayer(mp.player);
        setMatches(await api.getMyMatches());
        if (mp.player) setProfile(await api.getPlayerProfile(mp.player.player_id));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const kpis = profile ? [
    { label: 'Mecze', value: profile.total_matches },
    { label: 'Gole', value: profile.total_goals },
    { label: 'Skuteczność', value: pct(profile.overall_effectiveness) },
    { label: 'Asysty', value: profile.total_assists },
    { label: 'Przejęcia', value: profile.total_steals },
    { label: 'Bloki', value: profile.total_blocks },
  ] : [];

  return (
    <div className="app-shell">
      <div className="app-main">
        <header>
          <span className="app-nav__logo">🤽</span>
          <strong>{clubName}</strong>
          <div style={{ marginLeft: 'auto' }} className="tag">
            <span className="small">{state.user?.email}</span>
            <button className="btn small danger" onClick={onLogout} style={{ padding: '2px 8px', minHeight: 24 }}>Wyloguj</button>
          </div>
        </header>

        <div className="wrap">
          {loading ? (
            <div className="muted" style={{ padding: 12 }}>Ładowanie...</div>
          ) : !player ? (
            <div className="card muted">
              Twoje konto nie jest jeszcze powiązane z profilem zawodnika. Skontaktuj się z trenerem.
            </div>
          ) : (
            <>
              <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span className="player-row__num">{player.number}</span>
                <div>
                  <div style={{ fontSize: 20, fontWeight: 700 }}>{player.name}</div>
                  <div className="muted small">
                    {player.birth_year ? `rocznik ${player.birth_year} · ` : ''}
                    {(player.age_categories || []).join(', ') || 'bez kategorii'}
                  </div>
                </div>
              </div>

              <div className="subhead">Moje statystyki</div>
              <div className="kpi-grid" style={{ marginBottom: 16 }}>
                {kpis.map(k => (
                  <div className="kpi-card" key={k.label}>
                    <div className="kpi-card__value">{k.value}</div>
                    <div className="kpi-card__label">{k.label}</div>
                  </div>
                ))}
              </div>

              <div className="card">
                <div className="subhead">Moje mecze ({matches.length})</div>
                {matches.length === 0 ? (
                  <div className="muted">Nie grałeś jeszcze w żadnym meczu</div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {matches.map(m => (
                      <div key={m.match_id} className="match-card">
                        <span className="result-badge" style={{ background: m.result ? RESULT[m.result]?.color : 'var(--border)' }}>
                          {m.result ? RESULT[m.result]?.label : '–'}
                        </span>
                        <div style={{ flex: 1, minWidth: 120 }}>
                          <div style={{ fontWeight: 600, fontSize: 14 }}>
                            vs {m.opponent || '—'} {m.is_mvp && <span title="MVP meczu">🏅</span>}
                          </div>
                          <div className="muted small">{m.date || '—'} · {m.ageCategory || 'bez kat.'}</div>
                        </div>
                        <div style={{ fontWeight: 700, color: 'var(--accent)' }}>{m.my_score}:{m.opp_score}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
