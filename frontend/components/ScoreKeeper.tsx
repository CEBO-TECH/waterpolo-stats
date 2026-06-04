'use client';

import { useCallback } from 'react';
import { api } from '@/lib/api';
import { AppState, Player, RecentEvent } from '@/lib/types';

type Props = {
  state: AppState;
  setState: (fn: (prev: AppState) => AppState) => void;
  attackMode: 'positional' | 'man_up';
  setAttackMode: (m: 'positional' | 'man_up') => void;
  showToast: (msg: string) => void;
  refreshEvents: () => void;
  refreshStats: () => void;
  note: string;
  setNote: (n: string) => void;
};

// Maps UI action → flag field name
function getFlag(action: string, isManUp: boolean): Record<string, number> {
  const flags: Record<string, number> = {};
  const suffix = isManUp ? 'man_up' : 'positional';

  switch (action) {
    case 'goal_play': flags[`is_goal_from_play_${suffix}`] = 1; break;
    case 'goal_counter': flags.is_goal_from_play_counter = 1; break;
    case 'goal_center': flags[`is_goal_from_center_${suffix}`] = 1; break;
    case 'goal_5m': flags.is_goal_5m_man_up = 1; break;
    case 'goal_penalty': flags.is_goal_5m_penalty = 1; break;
    case 'assist': flags[`is_assist_${suffix}`] = 1; break;
    case 'shot_saved': flags[`is_shot_saved_gk_${suffix}`] = 1; break;
    case 'miss_turnover': flags[`is_shot_miss_turnover_${suffix}`] = 1; break;
    case 'miss_reset': flags[`is_shot_miss_reset30_${suffix}`] = 1; break;
    case 'bad_pass_turnover': flags[`is_bad_pass_turnover_${suffix}`] = 1; break;
    case 'bad_pass_no': flags[`is_bad_pass_no_turnover_${suffix}`] = 1; break;
    case 'turnover_1v1': flags[`is_turnover_1v1_${suffix}`] = 1; break;
    case 'shot_clock': flags[`is_shot_clock_violation_${suffix}`] = 1; break;
    case 'excl_drawn_field': flags.is_excl_drawn_field_positional = 1; break;
    case 'excl_drawn_center': flags.is_excl_drawn_center_positional = 1; break;
    case 'penalty_drawn_field': flags.is_penalty_drawn_field_positional = 1; break;
    case 'penalty_drawn_center': flags.is_penalty_drawn_center_positional = 1; break;
    case 'no_return': flags[`is_no_return_${suffix}`] = 1; break;
    case 'excl_comm_field': flags[`is_excl_committed_field_${suffix}`] = 1; break;
    case 'excl_comm_center': flags[`is_excl_committed_center_${suffix}`] = 1; break;
    case 'pen_comm_field': flags[`is_penalty_committed_field_${suffix}`] = 1; break;
    case 'pen_comm_center': flags[`is_penalty_committed_center_${suffix}`] = 1; break;
    case 'shot_saved_def': flags[`is_shot_saved_gk_def_${suffix}`] = 1; break;
    case 'steal': flags[`is_steal_${suffix}`] = 1; break;
    case 'block': flags[`is_block_hand_${suffix}`] = 1; break;
    case 'no_block': flags[`is_no_block_${suffix}`] = 1; break;
  }
  return flags;
}

export default function ScoreKeeper({
  state, setState, attackMode, setAttackMode, showToast,
  refreshEvents, refreshStats, note, setNote,
}: Props) {
  const isActive = state.matches.find(m => m.match_id === state.settings?.ActiveMatch)?.status === 'active';

  const selectPlayer = (p: Player) => {
    if (!isActive) return;
    setState(prev => ({ ...prev, selected: p }));
  };

  const submitEvent = async (action: string) => {
    if (!state.selected) return showToast('Wybierz zawodnika');
    if (!isActive) return showToast('Mecz zakończony');

    const flags = getFlag(action, attackMode === 'man_up');

    try {
      await api.createEvents([{
        player_id: state.selected.player_id,
        player_name: state.selected.name,
        note,
        ...flags,
      }]);
      setNote('');
      showToast('Zapisano');
      refreshEvents();
    } catch (e: any) {
      showToast(e.message || 'Błąd');
    }
  };

  const deleteEvent = async (eventId: string) => {
    try {
      await api.deleteEvent(eventId);
      showToast('Usunięto');
      refreshEvents();
    } catch (e: any) {
      showToast(e.message || 'Błąd');
    }
  };

  const Btn = ({ action, label }: { action: string; label: string }) => (
    <button className="btn" onClick={() => submitEvent(action)}>{label}</button>
  );

  return (
    <div className="main-layout">
      {/* Player sidebar */}
      <div className="players-sidebar">
        {state.rosterActive.length === 0 ? (
          <div className="muted" style={{ padding: 12 }}>Brak składu</div>
        ) : (
          state.rosterActive.map(p => (
            <div
              key={p.player_id}
              className={`player${state.selected?.player_id === p.player_id ? ' active' : ''}${!isActive ? ' disabled' : ''}`}
              onClick={() => selectPlayer(p)}
            >
              <div className="num">{p.number}</div>
              <div className="name">{p.name}</div>
            </div>
          ))
        )}
      </div>

      {/* Actions */}
      <div className="actions-main">
        <div className="panel">
          <div className="muted" style={{ marginBottom: 12 }}>
            Wybrany: <span style={{ color: 'var(--accent)', fontWeight: 600 }}>
              {state.selected ? `#${state.selected.number} ${state.selected.name}` : '—'}
            </span>
          </div>

          {/* Attack mode toggle */}
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 20 }}>
            <div className="toggle-switch">
              <div
                className={`toggle-option${attackMode === 'positional' ? ' active' : ''}`}
                onClick={() => setAttackMode('positional')}
              >
                Pozycyjny
              </div>
              <div
                className={`toggle-option${attackMode === 'man_up' ? ' active man-up' : ''}`}
                onClick={() => setAttackMode('man_up')}
              >
                Przewaga
              </div>
            </div>
          </div>

          {/* Note input */}
          <div style={{ marginBottom: 16 }}>
            <input
              placeholder="Notatka (opcjonalnie)..."
              value={note}
              onChange={e => setNote(e.target.value)}
              style={{ fontSize: 13 }}
            />
          </div>
        </div>

        {/* Attack buttons */}
        <div className={`card${attackMode === 'man_up' ? ' man-up-mode' : ''}`}>
          <div className="subhead">Atak — {attackMode === 'man_up' ? 'Przewaga' : 'Pozycyjny'}</div>

          <div className="subhead">Bramki</div>
          <div className="grid">
            {attackMode === 'positional' ? (
              <>
                <Btn action="goal_play" label="z akcji" />
                <Btn action="goal_counter" label="z kontrataku" />
                <Btn action="goal_center" label="z centra" />
              </>
            ) : (
              <>
                <Btn action="goal_center" label="z centra" />
                <Btn action="goal_5m" label="z 5 metrów" />
              </>
            )}
          </div>

          <div className="subhead">Asysta</div>
          <div className="grid">
            <Btn action="assist" label="Asysta" />
          </div>

          <div className="subhead">Strata piłki</div>
          <div className="grid">
            <Btn action="shot_saved" label="Obrona bramkarza" />
            <Btn action="miss_turnover" label="Niecelny rzut — strata" />
            <Btn action="miss_reset" label="Niecelny rzut — 30s" />
            <Btn action="bad_pass_turnover" label="Złe podanie — strata" />
            <Btn action="bad_pass_no" label="Złe podanie — bez straty" />
            <Btn action="turnover_1v1" label="Strata 1:1" />
            <Btn action="shot_clock" label="Koniec czasu" />
          </div>

          {attackMode === 'positional' && (
            <>
              <div className="subhead">Sprowokowanie</div>
              <div className="grid">
                <Btn action="excl_drawn_field" label="Wykluczenie — w polu" />
                <Btn action="excl_drawn_center" label="Wykluczenie — z centra" />
                <Btn action="penalty_drawn_field" label="Karny — w polu" />
                <Btn action="penalty_drawn_center" label="Karny — z centra" />
              </div>

              <div className="subhead">Rzuty karne</div>
              <div className="grid">
                <button className="btn primary" onClick={() => submitEvent('goal_penalty')}>
                  Bramka z karnego
                </button>
              </div>
            </>
          )}
        </div>

        {/* Defense buttons */}
        <div className="card">
          <div className="subhead">Obrona</div>
          <div className="grid">
            <Btn action="no_return" label="Brak powrotu" />
            <Btn action="excl_comm_field" label="Wykl. spowod. — w polu" />
            <Btn action="excl_comm_center" label="Wykl. spowod. — z centra" />
            <Btn action="pen_comm_field" label="Karny spowod. — w polu" />
            <Btn action="pen_comm_center" label="Karny spowod. — z centra" />
            <Btn action="shot_saved_def" label="Obrona GK" />
            <Btn action="steal" label="Przejęcie" />
            <Btn action="block" label="Blok" />
            <Btn action="no_block" label="Brak bloku" />
          </div>
        </div>

        {/* Recent events */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <div className="subhead" style={{ margin: 0 }}>Ostatnie akcje</div>
            <button className="btn small" onClick={refreshEvents}>Odśwież</button>
          </div>
          <div className="events-list">
            {state.recentEvents.length === 0 ? (
              <div className="muted">Brak akcji</div>
            ) : (
              state.recentEvents.map(ev => (
                <div key={ev.id} className="event-item">
                  <span className="event-quarter">Q{ev.quarter}</span>
                  <span className="event-action">{ev.action}</span>
                  <span className="event-player">{ev.player_name}</span>
                  {isActive && (
                    <button
                      className="btn small danger"
                      onClick={() => deleteEvent(ev.id)}
                    >
                      ✕
                    </button>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
