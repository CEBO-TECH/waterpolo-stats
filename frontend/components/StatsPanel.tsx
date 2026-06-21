'use client';

import { Fragment, useState, useEffect, useMemo } from 'react';
import { api } from '@/lib/api';
import { AppState, Match, AGE_CATEGORIES } from '@/lib/types';
import { Bars, GroupedBars, MultiSeriesBars, SERIES_PALETTE } from '@/components/Charts';

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

const pct = (v: number) => `${Math.round((v || 0) * 100)}%`;
const matchLabel = (m?: Match) => m ? `vs ${m.opponent || '—'}` : '—';

type Props = {
  state: AppState;
  showToast: (msg: string) => void;
};

export default function StatsPanel({ state, showToast }: Props) {
  const matches = state.matches;
  const players = state.players;
  const catNames = state.ageCategories.length
    ? state.ageCategories.map(c => c.name)
    : AGE_CATEGORIES;

  // ── Filters ──
  const [catFilter, setCatFilter] = useState('all');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [playerId, setPlayerId] = useState('all');
  const [selectedIds, setSelectedIds] = useState<string[]>(
    () => (state.settings?.ActiveMatch ? [state.settings.ActiveMatch] : []),
  );
  const [tab, setTab] = useState<'table' | 'charts' | 'compare'>('table');

  // Whether a match passes the current category + date-range filter.
  const inPool = (m: Match, cat: string, from: string, to: string) => {
    if (cat !== 'all' && (m.ageCategory || '') !== cat) return false;
    if (from && (m.date || '') < from) return false;
    if (to && (m.date || '') > to) return false;
    return true;
  };

  const pool = useMemo(
    () => matches.filter(m => inPool(m, catFilter, dateFrom, dateTo)),
    [matches, catFilter, dateFrom, dateTo],
  );
  const poolIds = useMemo(() => pool.map(m => m.match_id), [pool]);
  const matchById = useMemo(() => {
    const map: Record<string, Match> = {};
    matches.forEach(m => { map[m.match_id] = m; });
    return map;
  }, [matches]);

  // Changing a *scope* filter (category / date) re-selects the whole resulting
  // pool — that's what "cała kategoria" / "zakres dat" mean. Individual matches
  // can then be toggled off.
  const applyCat = (cat: string) => {
    setCatFilter(cat);
    setSelectedIds(matches.filter(m => inPool(m, cat, dateFrom, dateTo)).map(m => m.match_id));
  };
  const applyDate = (from: string, to: string) => {
    setDateFrom(from);
    setDateTo(to);
    setSelectedIds(matches.filter(m => inPool(m, catFilter, from, to)).map(m => m.match_id));
  };

  const toggleMatch = (id: string) =>
    setSelectedIds(prev => (prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]));
  const selectAll = () => setSelectedIds(poolIds);
  const clearSel = () => setSelectedIds([]);

  // ── Data ──
  const [single, setSingle] = useState<any>(null);
  const [multi, setMulti] = useState<any>(null);
  const [player, setPlayer] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const selKey = selectedIds.join(',');
  const isSingle = selectedIds.length === 1;
  const isPlayer = playerId !== 'all';

  useEffect(() => {
    let active = true;
    (async () => {
      if (selectedIds.length === 0) {
        setSingle(null); setMulti(null); setPlayer(null);
        return;
      }
      setLoading(true);
      try {
        const [m, s, p] = await Promise.all([
          api.getMultiStats(selectedIds),
          selectedIds.length === 1 ? api.getMatchStats(selectedIds[0]) : Promise.resolve(null),
          isPlayer ? api.getPlayerProfile(playerId) : Promise.resolve(null),
        ]);
        if (!active) return;
        setMulti(m); setSingle(s); setPlayer(p);
      } catch {
        if (active) showToast('Błąd ładowania statystyk');
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => { active = false; };
  }, [selKey, playerId]); // eslint-disable-line

  // Player trend, restricted to the selected matches.
  const playerTrend = useMemo(
    () => (player?.match_trend || []).filter((m: any) => selectedIds.includes(m.match_id)),
    [player, selKey], // eslint-disable-line
  );

  const TABS: { key: typeof tab; label: string }[] = [
    { key: 'table', label: 'Tabela' },
    { key: 'charts', label: 'Wykresy' },
    { key: 'compare', label: 'Porównaj mecze' },
  ];

  // ── Single-match quarter sub-filter ──
  const [quarter, setQuarter] = useState('all');

  const empty = selectedIds.length === 0;

  return (
    <div className="wrap">
      {/* ── Filter bar ── */}
      <div className="card">
        <div className="subhead">Zakres statystyk</div>
        <div className="stats-filters">
          <div className="stats-filters__row">
            <div className="stats-filters__field">
              <label>Kategoria wiekowa</label>
              <select className="players-toolbar__select" value={catFilter} onChange={e => applyCat(e.target.value)}>
                <option value="all">Wszystkie kategorie</option>
                {catNames.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div className="stats-filters__field">
              <label>Od (data)</label>
              <input className="players-toolbar__select" type="date" value={dateFrom} onChange={e => applyDate(e.target.value, dateTo)} />
            </div>
            <div className="stats-filters__field">
              <label>Do (data)</label>
              <input className="players-toolbar__select" type="date" value={dateTo} onChange={e => applyDate(dateFrom, e.target.value)} />
            </div>
            <div className="stats-filters__field">
              <label>Zawodnik</label>
              <select className="players-toolbar__select" value={playerId} onChange={e => setPlayerId(e.target.value)}>
                <option value="all">Wszyscy zawodnicy</option>
                {players.map(p => <option key={p.player_id} value={p.player_id}>{p.number ? `#${p.number} ` : ''}{p.name}</option>)}
              </select>
            </div>
          </div>

          <div className="stats-toolbar">
            <span className="muted small">
              Mecze: <strong style={{ color: 'var(--accent)' }}>{selectedIds.length}</strong> wybrane
              {pool.length !== matches.length && ` (z ${pool.length} w filtrze)`}
            </span>
            <div style={{ display: 'flex', gap: 6, marginLeft: 'auto' }}>
              <button className="btn small" onClick={selectAll} disabled={pool.length === 0}>Zaznacz wszystkie</button>
              <button className="btn small" onClick={clearSel} disabled={selectedIds.length === 0}>Wyczyść</button>
            </div>
          </div>

          <div className="match-select-list">
            {pool.map(m => (
              <div
                key={m.match_id}
                className={`match-select-item${selectedIds.includes(m.match_id) ? ' on' : ''}`}
                onClick={() => toggleMatch(m.match_id)}
              >
                <input type="checkbox" checked={selectedIds.includes(m.match_id)} onChange={() => {}} style={{ accentColor: 'var(--accent)' }} />
                <span>vs {m.opponent || '—'} <span className="muted">· {m.date || '—'} · {m.ageCategory || 'bez kat.'}</span></span>
              </div>
            ))}
            {pool.length === 0 && <div className="muted small">Brak meczów dla wybranego filtra</div>}
          </div>
        </div>
      </div>

      {/* ── Tabs ── */}
      <div className="tabs">
        {TABS.map(t => (
          <button key={t.key} className={`btn small${tab === t.key ? ' primary' : ''}`} onClick={() => setTab(t.key)}>
            {t.label}
          </button>
        ))}
      </div>

      {/* ── Result ── */}
      {empty ? (
        <div className="card muted">Wybierz mecz, kategorię lub zakres dat, aby zobaczyć statystyki.</div>
      ) : loading ? (
        <div className="card muted">Ładowanie statystyk…</div>
      ) : tab === 'compare' ? (
        <CompareView multi={multi} matchById={matchById} selectedIds={selectedIds} />
      ) : tab === 'charts' ? (
        isPlayer
          ? <PlayerCharts trend={playerTrend} />
          : isSingle && single
            ? <ChartsView stats={single} />
            : <MultiCharts multi={multi} />
      ) : (
        isPlayer
          ? <PlayerTable trend={playerTrend} />
          : isSingle && single
            ? <TableView stats={single} quarter={quarter} setQuarter={setQuarter} />
            : <MultiTable multi={multi} matchById={matchById} />
      )}
    </div>
  );
}

// ─── Single match: per-player flag table ───
function TableView({ stats, quarter, setQuarter }: { stats: any; quarter: string; setQuarter: (q: string) => void }) {
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
      </div>
      <div className="stats-table-wrap">
        <table className="stats-table">
          <thead>
            <tr>
              <th>Statystyka</th>
              {players.map((p: any) => <th key={p.player_id}>{p.number ? `#${p.number} ` : ''}{p.name}</th>)}
              <th style={{ background: 'var(--bg-hover)' }}>Razem</th>
            </tr>
          </thead>
          <tbody>
            {FLAG_GROUPS.map(group => (
              <Fragment key={group.name}>
                <tr className="stats-group-header">
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
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

// ─── Single match: charts ───
// Metrics the user can plot. Each is a named group of flags with a fixed colour.
const CHART_METRICS: { key: string; name: string; color: string; flags: string[] }[] = [
  { key: 'goals', name: 'Bramki', color: 'var(--green)', flags: GOAL_FLAGS_FE },
  { key: 'assists', name: 'Asysty', color: 'var(--accent)', flags: ['is_assist_positional', 'is_assist_man_up'] },
  { key: 'turnovers', name: 'Straty', color: 'var(--red)', flags: TURNOVER_FLAGS_FE },
  { key: 'gk_saves', name: 'Obrony GK', color: '#38bdf8', flags: ['is_shot_saved_gk_def_positional', 'is_shot_saved_gk_def_man_up'] },
  { key: 'excl_drawn', name: 'Sprow. wykluczenia', color: 'var(--orange)', flags: ['is_excl_drawn_field_positional', 'is_excl_drawn_center_positional'] },
  { key: 'steals', name: 'Przejęcia', color: '#a78bfa', flags: ['is_steal_positional', 'is_steal_man_up'] },
  { key: 'blocks', name: 'Bloki', color: '#f472b6', flags: ['is_block_hand_positional', 'is_block_hand_man_up'] },
];

function ChartsView({ stats }: { stats: any }) {
  const players = stats.players || [];
  const [metricKeys, setMetricKeys] = useState<string[]>(['goals', 'turnovers']);
  const [xAxis, setXAxis] = useState<'players' | 'quarters'>('players');

  const metrics = CHART_METRICS.filter(m => metricKeys.includes(m.key));
  const toggleMetric = (k: string) =>
    setMetricKeys(prev => (prev.includes(k) ? prev.filter(x => x !== k) : [...prev, k]));

  let categories: string[] = [];
  let series: { name: string; color: string; values: number[] }[] = [];

  if (xAxis === 'quarters') {
    const qs = ['1', '2', '3', '4'];
    categories = ['Q1', 'Q2', 'Q3', 'Q4'];
    series = metrics.map(m => ({
      name: m.name, color: m.color,
      values: qs.map(q => sumFlags(stats.totalsByQ?.[q], m.flags)),
    }));
  } else if (xAxis === 'players') {
    const rows = players
      .map((p: any) => ({
        p,
        total: metrics.reduce((s, m) => s + sumFlags(stats.perPlayerAll?.[p.player_id], m.flags), 0),
      }))
      .filter((r: any) => r.total > 0)
      .sort((a: any, b: any) => b.total - a.total);
    categories = rows.map((r: any) => (r.p.number ? `#${r.p.number}` : r.p.name.split(' ').slice(-1)[0]));
    series = metrics.map(m => ({
      name: m.name, color: m.color,
      values: rows.map((r: any) => sumFlags(stats.perPlayerAll?.[r.p.player_id], m.flags)),
    }));
  }

  const tab = (key: typeof xAxis, label: string) => (
    <div className={`toggle-option${xAxis === key ? ' active' : ''}`} onClick={() => setXAxis(key)}>{label}</div>
  );

  return (
    <div className="card">
      <div className="subhead">Wykresy</div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 10 }}>
        <span className="muted small">Oś X:</span>
        <div className="toggle-switch">
          {tab('players', 'Zawodnicy')}
          {tab('quarters', 'Kwarty')}
        </div>
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 14 }}>
        {CHART_METRICS.map(m => {
          const on = metricKeys.includes(m.key);
          return (
            <button key={m.key} className={`btn small${on ? ' primary' : ''}`} onClick={() => toggleMetric(m.key)}>
              <span style={{ color: on ? undefined : m.color }}>■</span> {m.name}
            </button>
          );
        })}
      </div>

      {metrics.length === 0 ? (
        <div className="muted small">Wybierz co najmniej jedną cechę.</div>
      ) : categories.length === 0 ? (
        <div className="muted small">Brak danych dla wybranych cech.</div>
      ) : (
        <MultiSeriesBars categories={categories} series={series} />
      )}
    </div>
  );
}

// ─── Many matches: aggregate table (per-match rows) ───
function MultiTable({ multi, matchById }: { multi: any; matchById: Record<string, Match> }) {
  if (!multi) return <div className="card muted">Brak danych</div>;
  const t = multi.totals || {};
  const KPIS = [
    { label: 'Mecze', value: multi.match_count },
    { label: 'Bramki', value: t.goals },
    { label: 'Asysty', value: t.assists },
    { label: 'Straty', value: t.turnovers },
    { label: 'Przejęcia', value: t.steals },
    { label: 'Indeks of.', value: t.of_index },
    { label: 'Indeks def.', value: t.def_index },
  ];
  return (
    <>
      <div className="kpi-grid" style={{ marginBottom: 16 }}>
        {KPIS.map(k => (
          <div className="kpi-card" key={k.label}>
            <div className="kpi-card__value">{k.value ?? '·'}</div>
            <div className="kpi-card__label">{k.label}</div>
          </div>
        ))}
      </div>
      <div className="card">
        <div className="subhead">Mecze ({multi.trend?.length || 0})</div>
        <div className="stats-table-wrap">
          <table className="stats-table">
            <thead>
              <tr>
                <th>Mecz</th><th>Wynik</th><th>Bramki</th><th>Straty</th>
                <th>Przejęcia</th><th>Indeks of.</th><th>Indeks def.</th>
              </tr>
            </thead>
            <tbody>
              {(multi.trend || []).map((m: any) => (
                <tr key={m.match_id}>
                  <td style={{ textAlign: 'left', whiteSpace: 'nowrap' }}>
                    {m.date} <span className="muted">vs {m.opponent || '—'}</span>
                  </td>
                  <td>{m.my_score}:{m.opp_score}</td>
                  <td>{m.goals}</td>
                  <td>{m.turnovers}</td>
                  <td>{m.steals}</td>
                  <td style={{ color: m.of_index >= 0 ? 'var(--green)' : 'var(--red)', fontWeight: 700 }}>{m.of_index > 0 ? '+' : ''}{m.of_index}</td>
                  <td style={{ color: m.def_index >= 0 ? 'var(--green)' : 'var(--red)', fontWeight: 700 }}>{m.def_index > 0 ? '+' : ''}{m.def_index}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}

// ─── Many matches: charts ───
function MultiCharts({ multi }: { multi: any }) {
  if (!multi) return <div className="card muted">Brak danych</div>;
  return (
    <>
      <div className="card">
        <div className="subhead">Bramki per mecz (tendencja)</div>
        <Bars data={(multi.trend || []).map((t: any) => ({ label: t.opponent || '—', value: t.goals }))} color="var(--accent)" />
      </div>
      <div className="card">
        <div className="subhead">Rozkład czasowy (suma kwart)</div>
        <GroupedBars
          categories={['Q1', 'Q2', 'Q3', 'Q4']}
          seriesA={{ name: 'Bramki', color: 'var(--green)', values: (multi.by_quarter || []).map((q: any) => q.goals) }}
          seriesB={{ name: 'Straty', color: 'var(--red)', values: (multi.by_quarter || []).map((q: any) => q.turnovers) }}
        />
      </div>
    </>
  );
}

// ─── Compare: matches overlaid (columns + overlaid bars) ───
function CompareView({ multi, matchById, selectedIds }: { multi: any; matchById: Record<string, Match>; selectedIds: string[] }) {
  if (selectedIds.length < 2)
    return <div className="card muted">Zaznacz co najmniej 2 mecze, aby je porównać.</div>;
  if (!multi?.trend?.length) return <div className="card muted">Brak danych</div>;

  const trend: any[] = multi.trend;
  const colLabel = (t: any) => `vs ${t.opponent || '—'}`;

  // Rows shown in the overlaid comparison table.
  const ROWS: { label: string; get: (t: any) => any; signed?: boolean; chart?: boolean }[] = [
    { label: 'Wynik', get: t => `${t.my_score}:${t.opp_score}` },
    { label: 'Bramki', get: t => t.goals, chart: true },
    { label: 'Straty', get: t => t.turnovers, chart: true },
    { label: 'Przejęcia', get: t => t.steals, chart: true },
    { label: 'Indeks of.', get: t => t.of_index, signed: true },
    { label: 'Indeks def.', get: t => t.def_index, signed: true },
  ];

  const chartRows = ROWS.filter(r => r.chart);
  const series = trend.map((t, i) => ({
    name: colLabel(t),
    color: SERIES_PALETTE[i % SERIES_PALETTE.length],
    values: chartRows.map(r => Number(r.get(t)) || 0),
  }));

  return (
    <>
      <div className="card">
        <div className="subhead">Porównanie — wykres nałożony</div>
        <MultiSeriesBars categories={chartRows.map(r => r.label)} series={series} />
      </div>

      <div className="card">
        <div className="subhead">Porównanie — tabela</div>
        <div className="stats-table-wrap">
          <table className="stats-table">
            <thead>
              <tr>
                <th>Statystyka</th>
                {trend.map((t, i) => (
                  <th key={t.match_id}>
                    <span style={{ color: SERIES_PALETTE[i % SERIES_PALETTE.length] }}>■</span> {colLabel(t)}
                    <div className="muted small">{t.date}</div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {ROWS.map(row => (
                <tr key={row.label}>
                  <td>{row.label}</td>
                  {trend.map(t => {
                    const v = row.get(t);
                    const style = row.signed
                      ? { color: (Number(v) >= 0 ? 'var(--green)' : 'var(--red)'), fontWeight: 700 }
                      : undefined;
                    const display = row.signed && Number(v) > 0 ? `+${v}` : v;
                    return <td key={t.match_id} style={style}>{display}</td>;
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}

// ─── Player-focused: KPI + per-match table ───
function PlayerTable({ trend }: { trend: any[] }) {
  if (trend.length === 0) return <div className="card muted">Brak danych zawodnika w wybranych meczach.</div>;
  const agg = trend.reduce((a, m) => ({
    goals: a.goals + (m.goals || 0), shots: a.shots + (m.shots || 0),
    assists: a.assists + (m.assists || 0), turnovers: a.turnovers + (m.turnovers || 0),
    exclusions: a.exclusions + (m.exclusions || 0), steals: a.steals + (m.steals || 0),
    blocks: a.blocks + (m.blocks || 0),
  }), { goals: 0, shots: 0, assists: 0, turnovers: 0, exclusions: 0, steals: 0, blocks: 0 });
  const eff = agg.shots ? agg.goals / agg.shots : 0;
  const KPIS = [
    { label: 'Mecze', value: trend.length },
    { label: 'Gole', value: agg.goals },
    { label: 'Skuteczność', value: pct(eff) },
    { label: 'Asysty', value: agg.assists },
    { label: 'Straty', value: agg.turnovers },
    { label: 'Wykluczenia', value: agg.exclusions },
    { label: 'Przejęcia', value: agg.steals },
    { label: 'Bloki', value: agg.blocks },
  ];
  return (
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
        <div className="subhead">Tendencja per mecz</div>
        <div className="stats-table-wrap">
          <table className="stats-table">
            <thead>
              <tr><th>Mecz</th><th>Gole</th><th>Rzuty</th><th>Sk.</th><th>As.</th><th>Str.</th><th>Wykl.</th><th>Prz.</th><th>Bloki</th></tr>
            </thead>
            <tbody>
              {trend.map((m: any) => (
                <tr key={m.match_id}>
                  <td style={{ textAlign: 'left', whiteSpace: 'nowrap' }}>{m.match_date} <span className="muted">vs {m.opponent || '—'}</span></td>
                  <td>{m.goals || '·'}</td>
                  <td>{m.shots || '·'}</td>
                  <td>{pct(m.shot_effectiveness)}</td>
                  <td>{m.assists || '·'}</td>
                  <td>{m.turnovers || '·'}</td>
                  <td>{m.exclusions || '·'}</td>
                  <td>{m.steals || '·'}</td>
                  <td>{m.blocks || '·'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}

// ─── Player-focused: charts ───
function PlayerCharts({ trend }: { trend: any[] }) {
  if (trend.length === 0) return <div className="card muted">Brak danych zawodnika w wybranych meczach.</div>;
  const goals = trend.map((m: any) => ({ label: m.opponent || '—', value: m.goals || 0 }));
  const eff = trend.map((m: any) => ({ label: m.opponent || '—', value: Math.round((m.shot_effectiveness || 0) * 100) }));
  return (
    <>
      <div className="card">
        <div className="subhead">Bramki per mecz</div>
        <Bars data={goals} color="var(--green)" />
      </div>
      <div className="card">
        <div className="subhead">Skuteczność rzutów per mecz</div>
        <Bars data={eff} color="var(--accent)" unit="%" />
      </div>
    </>
  );
}
