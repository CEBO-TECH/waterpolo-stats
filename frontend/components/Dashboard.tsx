'use client';

import { useEffect, useState, useCallback } from 'react';
import { api } from '@/lib/api';
import { AppState, Mode, AGE_CATEGORIES } from '@/lib/types';

type Props = {
  state: AppState;
  showToast: (m: string) => void;
  goToMode: (m: Mode) => void;
  setMatch: (id: string) => void;
};

const RESULT: Record<string, { label: string; color: string }> = {
  W: { label: 'Z', color: 'var(--green)' },
  L: { label: 'P', color: 'var(--red)' },
  D: { label: 'R', color: 'var(--yellow)' },
};

export default function Dashboard({ state, showToast, goToMode, setMatch }: Props) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [filterCat, setFilterCat] = useState<string>('all');

  const catNames = state.ageCategories.length
    ? state.ageCategories.map(c => c.name)
    : AGE_CATEGORIES;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const d = await api.getDashboard(filterCat === 'all' ? undefined : filterCat);
      setData(d);
    } catch {
      showToast('Błąd ładowania pulpitu');
    } finally {
      setLoading(false);
    }
  }, [filterCat, showToast]);

  useEffect(() => { load(); }, [load]);

  const resumeMatch = (matchId: string, status: string) => {
    setMatch(matchId);
    goToMode(status === 'active' ? 'score' : 'stats');
  };

  const am = data?.active_match;

  return (
    <div className="wrap">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap', marginBottom: 4 }}>
        <div className="subhead" style={{ margin: 0 }}>Pulpit</div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <select
            className="players-toolbar__select"
            value={filterCat}
            onChange={e => setFilterCat(e.target.value)}
          >
            <option value="all">Wszystkie kategorie</option>
            {catNames.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <button className="btn primary" onClick={() => goToMode('admin')}>+ Nowy mecz</button>
        </div>
      </div>

      {!data ? (
        <div className="muted" style={{ padding: 12 }}>{loading ? 'Ładowanie...' : 'Brak danych'}</div>
      ) : (
        <>
          {/* Active match */}
          {am ? (
            <div className="card match-card--active" style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
              <div style={{ flex: 1, minWidth: 200 }}>
                <div className="muted small">{am.status === 'active' ? 'Aktywny mecz' : 'Ostatni mecz'}</div>
                <div style={{ fontSize: 18, fontWeight: 700 }}>vs {am.opponent || '—'}</div>
                <div className="muted small">{am.date || '—'} · {am.ageCategory || 'Bez kategorii'}</div>
              </div>
              <div style={{ fontSize: 26, fontWeight: 800, color: 'var(--accent)' }}>
                {am.my_score} : {am.opp_score}
              </div>
              <button className="btn primary" onClick={() => resumeMatch(am.match_id, am.status)}>
                {am.status === 'active' ? 'Wznów mecz' : 'Statystyki'}
              </button>
            </div>
          ) : (
            <div className="card muted">
              Brak aktywnego meczu. <span style={{ color: 'var(--accent)', cursor: 'pointer' }} onClick={() => goToMode('admin')}>Utwórz nowy mecz</span>.
            </div>
          )}

          {/* KPI */}
          <div className="kpi-grid" style={{ marginBottom: 16 }}>
            <div className="kpi-card">
              <div className="kpi-card__value">{data.total_matches}</div>
              <div className="kpi-card__label">Mecze</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-card__value" style={{ fontSize: 18 }}>
                <span style={{ color: 'var(--green)' }}>{data.wins}</span>
                {' · '}
                <span style={{ color: 'var(--red)' }}>{data.losses}</span>
                {' · '}
                <span style={{ color: 'var(--yellow)' }}>{data.draws}</span>
              </div>
              <div className="kpi-card__label">Z · P · R</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-card__value">{data.goals_for}:{data.goals_against}</div>
              <div className="kpi-card__label">Bramki</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-card__value">{data.goal_difference > 0 ? '+' : ''}{data.goal_difference}</div>
              <div className="kpi-card__label">Różnica</div>
            </div>
          </div>

          <div className="dash-cols">
            {/* Recent matches */}
            <div className="card">
              <div className="subhead">Ostatnie mecze</div>
              {data.recent_matches.length === 0 ? (
                <div className="muted">Brak meczów</div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {data.recent_matches.map((m: any) => (
                    <div
                      key={m.match_id}
                      className="match-card"
                      style={{ cursor: 'pointer' }}
                      onClick={() => resumeMatch(m.match_id, m.status)}
                    >
                      {m.result ? (
                        <span className="result-badge" style={{ background: RESULT[m.result]?.color }}>
                          {RESULT[m.result]?.label}
                        </span>
                      ) : (
                        <span className="result-badge" style={{ background: 'var(--border)' }}>–</span>
                      )}
                      <div style={{ flex: 1, minWidth: 120 }}>
                        <div style={{ fontWeight: 600, fontSize: 14 }}>vs {m.opponent || '—'}</div>
                        <div className="muted small">{m.date || '—'} · {m.ageCategory || 'Bez kategorii'}</div>
                      </div>
                      <div style={{ fontWeight: 700, color: 'var(--accent)' }}>{m.my_score}:{m.opp_score}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Top players */}
            <div className="card">
              <div className="subhead">Najlepsi zawodnicy</div>
              <div className="muted small" style={{ marginBottom: 6 }}>Strzelcy</div>
              <Ranking rows={data.top_scorers} unit="g" />
              <div className="muted small" style={{ margin: '14px 0 6px' }}>Asystenci</div>
              <Ranking rows={data.top_assistants} unit="a" />
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function Ranking({ rows, unit }: { rows: any[]; unit: string }) {
  if (!rows || rows.length === 0) return <div className="muted small">Brak danych</div>;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      {rows.map((r: any, i: number) => (
        <div key={r.player_id} className="rank-row">
          <span className="rank-row__pos">{i + 1}</span>
          <span style={{ flex: 1 }}>{r.player_name}</span>
          <span style={{ fontWeight: 700, color: 'var(--accent)' }}>{r.value}{unit}</span>
        </div>
      ))}
    </div>
  );
}
