'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { AppState } from '@/lib/types';
import { Bars, GroupedBars } from '@/components/Charts';

const GOAL_FLAGS_FE = [
  'is_goal_from_play_positional', 'is_goal_from_play_counter', 'is_goal_from_center_positional',
  'is_goal_from_center_man_up', 'is_goal_5m_man_up', 'is_goal_5m_penalty',
];
const TURNOVER_FLAGS_FE = [
  'is_bad_pass_turnover_positional', 'is_bad_pass_turnover_man_up',
  'is_turnover_1v1_positional', 'is_turnover_1v1_man_up',
  'is_shot_clock_violation_positional', 'is_shot_clock_violation_man_up',
  'is_shot_miss_turnover_positional', 'is_shot_miss_turnover_man_up',
];
const sumFlags = (obj: any, flags: string[]) => flags.reduce((s, f) => s + (obj?.[f] || 0), 0);

const FLAG_LABELS: Record<string, string> = {
  is_goal_from_play_positional: 'G z gry (poz.)',
  is_goal_from_play_counter: 'G z kontrataku',
  is_goal_from_center_positional: 'G z centra (poz.)',
  is_goal_from_center_man_up: 'G z centra (przew.)',
  is_goal_5m_man_up: 'G 5m (przew.)',
  is_goal_5m_penalty: 'G z karnego',
  is_assist_positional: 'Asysty (poz.)',
  is_assist_man_up: 'Asysty (przew.)',
  is_shot_saved_gk_positional: 'Obr. GK (poz.)',
  is_shot_saved_gk_man_up: 'Obr. GK (przew.)',
  is_shot_miss_turnover_positional: 'Rzut str. (poz.)',
  is_shot_miss_turnover_man_up: 'Rzut str. (przew.)',
  is_shot_miss_reset30_positional: 'Rzut 30s (poz.)',
  is_shot_miss_reset30_man_up: 'Rzut 30s (przew.)',
  is_bad_pass_turnover_positional: 'Złe pod. str. (poz.)',
  is_bad_pass_turnover_man_up: 'Złe pod. str. (przew.)',
  is_bad_pass_no_turnover_positional: 'Złe pod. (poz.)',
  is_bad_pass_no_turnover_man_up: 'Złe pod. (przew.)',
  is_turnover_1v1_positional: 'Strata 1:1 (poz.)',
  is_turnover_1v1_man_up: 'Strata 1:1 (przew.)',
  is_shot_clock_violation_positional: 'Koniec czasu (poz.)',
  is_shot_clock_violation_man_up: 'Koniec czasu (przew.)',
  is_excl_drawn_field_positional: 'Spr. wykl. pole (poz.)',
  is_excl_drawn_center_positional: 'Spr. wykl. centr (poz.)',
  is_penalty_drawn_field_positional: 'Spr. karny pole (poz.)',
  is_penalty_drawn_center_positional: 'Spr. karny centr (poz.)',
  is_no_return_positional: 'Brak powr. (poz.)',
  is_no_return_man_up: 'Brak powr. (przew.)',
  is_excl_committed_field_positional: 'Wykl. pole (poz.)',
  is_excl_committed_field_man_up: 'Wykl. pole (przew.)',
  is_excl_committed_center_positional: 'Wykl. centr (poz.)',
  is_excl_committed_center_man_up: 'Wykl. centr (przew.)',
  is_penalty_committed_field_positional: 'Karny pole (poz.)',
  is_penalty_committed_field_man_up: 'Karny pole (przew.)',
  is_penalty_committed_center_positional: 'Karny centr (poz.)',
  is_penalty_committed_center_man_up: 'Karny centr (przew.)',
  is_shot_saved_gk_def_positional: 'Obr. GK def (poz.)',
  is_shot_saved_gk_def_man_up: 'Obr. GK def (przew.)',
  is_steal_positional: 'Przejęcie (poz.)',
  is_steal_man_up: 'Przejęcie (przew.)',
  is_block_hand_positional: 'Blok (poz.)',
  is_block_hand_man_up: 'Blok (przew.)',
  is_no_block_positional: 'Brak bloku (poz.)',
  is_no_block_man_up: 'Brak bloku (przew.)',
};

// Group flags by category for display
const FLAG_GROUPS = [
  { name: 'Atak pozycyjny', flags: ['is_goal_from_play_positional', 'is_goal_from_play_counter', 'is_goal_from_center_positional', 'is_assist_positional', 'is_shot_saved_gk_positional', 'is_shot_miss_turnover_positional', 'is_shot_miss_reset30_positional', 'is_bad_pass_turnover_positional', 'is_bad_pass_no_turnover_positional', 'is_turnover_1v1_positional', 'is_shot_clock_violation_positional', 'is_excl_drawn_field_positional', 'is_excl_drawn_center_positional', 'is_penalty_drawn_field_positional', 'is_penalty_drawn_center_positional'] },
  { name: 'Atak przewaga', flags: ['is_goal_from_center_man_up', 'is_goal_5m_man_up', 'is_assist_man_up', 'is_shot_saved_gk_man_up', 'is_shot_miss_turnover_man_up', 'is_shot_miss_reset30_man_up', 'is_bad_pass_turnover_man_up', 'is_bad_pass_no_turnover_man_up', 'is_turnover_1v1_man_up', 'is_shot_clock_violation_man_up'] },
  { name: 'Rzuty karne', flags: ['is_goal_5m_penalty'] },
  { name: 'Obrona pozycyjna', flags: ['is_no_return_positional', 'is_excl_committed_field_positional', 'is_excl_committed_center_positional', 'is_penalty_committed_field_positional', 'is_penalty_committed_center_positional', 'is_shot_saved_gk_def_positional', 'is_steal_positional', 'is_block_hand_positional', 'is_no_block_positional'] },
  { name: 'Obrona przewaga', flags: ['is_no_return_man_up', 'is_excl_committed_field_man_up', 'is_excl_committed_center_man_up', 'is_penalty_committed_field_man_up', 'is_penalty_committed_center_man_up', 'is_shot_saved_gk_def_man_up', 'is_steal_man_up', 'is_block_hand_man_up', 'is_no_block_man_up'] },
];

type Props = {
  state: AppState;
  showToast: (msg: string) => void;
};

export default function StatsPanel({ state, showToast }: Props) {
  const [tab, setTab] = useState<'table' | 'charts' | 'compare'>('table');
  const [stats, setStats] = useState<any>(null);
  const [quarter, setQuarter] = useState('all');

  const matchId = state.settings?.ActiveMatch;

  const loadStats = useCallback(async () => {
    if (!matchId) return;
    try {
      setStats(await api.getMatchStats(matchId));
    } catch {
      showToast('Błąd ładowania statystyk');
    }
  }, [matchId, showToast]);

  useEffect(() => { loadStats(); }, [loadStats]);

  // ── Compare tab ──
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [multi, setMulti] = useState<any>(null);
  const [multiLoading, setMultiLoading] = useState(false);

  const toggleMatch = (id: string) =>
    setSelectedIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);

  const loadMulti = async () => {
    if (selectedIds.length === 0) return showToast('Zaznacz mecze');
    setMultiLoading(true);
    try {
      setMulti(await api.getMultiStats(selectedIds));
    } catch (e: any) {
      showToast(e.message || 'Błąd');
    } finally {
      setMultiLoading(false);
    }
  };

  const TABS: { key: typeof tab; label: string }[] = [
    { key: 'table', label: 'Tabela' },
    { key: 'charts', label: 'Wykresy' },
    { key: 'compare', label: 'Porównaj mecze' },
  ];

  return (
    <div className="wrap">
      <div className="tabs">
        {TABS.map(t => (
          <button key={t.key} className={`btn small${tab === t.key ? ' primary' : ''}`} onClick={() => setTab(t.key)}>
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'compare' ? (
        <CompareView
          matches={state.matches}
          selectedIds={selectedIds}
          toggleMatch={toggleMatch}
          loadMulti={loadMulti}
          multi={multi}
          loading={multiLoading}
        />
      ) : !stats ? (
        <div className="muted">Wybierz mecz aby zobaczyć statystyki</div>
      ) : tab === 'charts' ? (
        <ChartsView stats={stats} />
      ) : (
        <TableView stats={stats} quarter={quarter} setQuarter={setQuarter} reload={loadStats} />
      )}
    </div>
  );
}

function TableView({ stats, quarter, setQuarter, reload }: { stats: any; quarter: string; setQuarter: (q: string) => void; reload: () => void }) {
  const players = stats.players || [];
  const dataSource = quarter === 'all' ? stats.perPlayerAll : stats.perPlayerByQ?.[quarter] || {};
  const totals = quarter === 'all' ? stats.totalsAll : stats.totalsByQ?.[quarter] || {};
  const scores = stats.scores || {};
  return (
    <>
      <div className="card" style={{ display: 'flex', justifyContent: 'center', gap: 24, flexWrap: 'wrap' }}>
        {['1', '2', '3', '4', 'final'].map(q => (
          <div key={q} style={{ textAlign: 'center' }}>
            <div className="muted small">{q === 'final' ? 'Końcowy' : `Q${q}`}</div>
            <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--accent)' }}>
              {scores[q]?.my ?? 0} : {scores[q]?.opp ?? 0}
            </div>
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
        {['all', '1', '2', '3', '4'].map(q => (
          <button key={q} className={`btn small${quarter === q ? ' primary' : ''}`} onClick={() => setQuarter(q)}>
            {q === 'all' ? 'Wszystkie' : `Q${q}`}
          </button>
        ))}
        <button className="btn small" onClick={reload} style={{ marginLeft: 'auto' }}>Odśwież</button>
      </div>
      <div className="stats-table-wrap">
        <table className="stats-table">
          <thead>
            <tr>
              <th>Statystyka</th>
              {players.map((p: any) => <th key={p.player_id}>#{p.number} {p.name}</th>)}
              <th style={{ background: 'var(--bg-hover)' }}>Razem</th>
            </tr>
          </thead>
          <tbody>
            {FLAG_GROUPS.map(group => (
              <>
                <tr key={`g-${group.name}`} className="stats-group-header">
                  <td colSpan={players.length + 2}>{group.name}</td>
                </tr>
                {group.flags.map(flag => (
                  <tr key={flag}>
                    <td>{FLAG_LABELS[flag] || flag}</td>
                    {players.map((p: any) => {
                      const val = dataSource[p.player_id]?.[flag] || 0;
                      return (
                        <td key={p.player_id} style={{ color: val > 0 ? 'var(--accent)' : 'var(--fg-muted)' }}>
                          {val || '·'}
                        </td>
                      );
                    })}
                    <td style={{ fontWeight: 700, background: 'var(--bg-hover)' }}>{totals[flag] || '·'}</td>
                  </tr>
                ))}
              </>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

function ChartsView({ stats }: { stats: any }) {
  const players = stats.players || [];
  const goalsPerPlayer = players
    .map((p: any) => ({ label: `#${p.number}`, value: sumFlags(stats.perPlayerAll?.[p.player_id], GOAL_FLAGS_FE) }))
    .filter((d: any) => d.value > 0)
    .sort((a: any, b: any) => b.value - a.value);

  const quarters = ['1', '2', '3', '4'];
  const goalsByQ = quarters.map(q => sumFlags(stats.totalsByQ?.[q], GOAL_FLAGS_FE));
  const turnoversByQ = quarters.map(q => sumFlags(stats.totalsByQ?.[q], TURNOVER_FLAGS_FE));

  return (
    <>
      <div className="card">
        <div className="subhead">Bramki per zawodnik</div>
        {goalsPerPlayer.length === 0
          ? <div className="muted small">Brak bramek</div>
          : <Bars data={goalsPerPlayer} color="var(--green)" />}
      </div>
      <div className="card">
        <div className="subhead">Rozkład czasowy (kwarty)</div>
        <GroupedBars
          categories={['Q1', 'Q2', 'Q3', 'Q4']}
          seriesA={{ name: 'Bramki', color: 'var(--green)', values: goalsByQ }}
          seriesB={{ name: 'Straty', color: 'var(--red)', values: turnoversByQ }}
        />
      </div>
    </>
  );
}

function CompareView({ matches, selectedIds, toggleMatch, loadMulti, multi, loading }: {
  matches: any[]; selectedIds: string[]; toggleMatch: (id: string) => void;
  loadMulti: () => void; multi: any; loading: boolean;
}) {
  const KPIS = multi ? [
    { label: 'Bramki', value: multi.totals.goals },
    { label: 'Asysty', value: multi.totals.assists },
    { label: 'Straty', value: multi.totals.turnovers },
    { label: 'Przejęcia', value: multi.totals.steals },
    { label: 'Indeks of.', value: multi.totals.of_index },
    { label: 'Indeks def.', value: multi.totals.def_index },
  ] : [];

  return (
    <>
      <div className="card">
        <div className="subhead">Wybierz mecze ({selectedIds.length})</div>
        <div className="match-select-list">
          {matches.map(m => (
            <div
              key={m.match_id}
              className={`match-select-item${selectedIds.includes(m.match_id) ? ' on' : ''}`}
              onClick={() => toggleMatch(m.match_id)}
            >
              <input type="checkbox" checked={selectedIds.includes(m.match_id)} onChange={() => {}} style={{ accentColor: 'var(--accent)' }} />
              <span>vs {m.opponent || '—'} <span className="muted">· {m.date || '—'} · {m.ageCategory || 'bez kat.'}</span></span>
            </div>
          ))}
          {matches.length === 0 && <div className="muted small">Brak meczów</div>}
        </div>
        <button className="btn primary" onClick={loadMulti} disabled={loading} style={{ marginTop: 12 }}>
          {loading ? 'Liczenie...' : 'Pokaż statystyki'}
        </button>
      </div>

      {multi && (
        <>
          <div className="kpi-grid" style={{ marginBottom: 16 }}>
            {KPIS.map(k => (
              <div className="kpi-card" key={k.label}>
                <div className="kpi-card__value">{k.value}</div>
                <div className="kpi-card__label">{k.label}</div>
              </div>
            ))}
          </div>

          <div className="card">
            <div className="subhead">Bramki per mecz (tendencja)</div>
            <Bars
              data={multi.trend.map((t: any) => ({ label: t.opponent || '—', value: t.goals }))}
              color="var(--accent)"
            />
          </div>

          <div className="card">
            <div className="subhead">Rozkład czasowy (suma kwart)</div>
            <GroupedBars
              categories={['Q1', 'Q2', 'Q3', 'Q4']}
              seriesA={{ name: 'Bramki', color: 'var(--green)', values: multi.by_quarter.map((q: any) => q.goals) }}
              seriesB={{ name: 'Straty', color: 'var(--red)', values: multi.by_quarter.map((q: any) => q.turnovers) }}
            />
          </div>

          <div className="card">
            <div className="subhead">Ofensywność / defensywność per mecz</div>
            <div className="stats-table-wrap">
              <table className="stats-table">
                <thead>
                  <tr><th>Mecz</th><th>Bramki</th><th>Straty</th><th>Indeks of.</th><th>Indeks def.</th></tr>
                </thead>
                <tbody>
                  {multi.trend.map((t: any) => (
                    <tr key={t.match_id}>
                      <td style={{ textAlign: 'left', whiteSpace: 'nowrap' }}>{t.date} <span className="muted">vs {t.opponent || '—'}</span></td>
                      <td>{t.goals}</td>
                      <td>{t.turnovers}</td>
                      <td style={{ color: t.of_index >= 0 ? 'var(--green)' : 'var(--red)', fontWeight: 700 }}>{t.of_index > 0 ? '+' : ''}{t.of_index}</td>
                      <td style={{ color: t.def_index >= 0 ? 'var(--green)' : 'var(--red)', fontWeight: 700 }}>{t.def_index > 0 ? '+' : ''}{t.def_index}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </>
  );
}
