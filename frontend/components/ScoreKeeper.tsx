'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { AppState, Player, RecentEvent } from '@/lib/types';
import VideoModal from '@/components/VideoModal';
import VoiceNotes from '@/components/VoiceNotes';

type PlaytimeEntry = { seconds: number; on_water: boolean; stint_start: string | null };

function fmtTime(total: number): string {
  const s = Math.max(0, Math.floor(total));
  const m = Math.floor(s / 60);
  return `${m}:${String(s % 60).padStart(2, '0')}`;
}

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
  const matchId = state.settings?.ActiveMatch || '';
  const youtube = state.youtube;
  const streamSynced = !!youtube?.stream_start_time;

  const [video, setVideo] = useState<{ video_id: string; seek_seconds: number } | null>(null);
  const [streamBusy, setStreamBusy] = useState(false);

  const [playtime, setPlaytime] = useState<Record<string, PlaytimeEntry>>({});
  const [playtimeAt, setPlaytimeAt] = useState<number>(Date.now());
  const [nowTick, setNowTick] = useState<number>(Date.now());

  const loadPlaytime = useCallback(async () => {
    if (!matchId) return;
    const data = await api.getPlaytime(matchId);
    setPlaytime(data.players || {});
    setPlaytimeAt(Date.now());
  }, [matchId]);

  useEffect(() => { loadPlaytime(); }, [loadPlaytime]);

  // Tick every second so the on-water counters advance.
  useEffect(() => {
    const id = setInterval(() => setNowTick(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  const displaySeconds = (playerId: string): number => {
    const e = playtime[playerId];
    if (!e) return 0;
    const extra = e.on_water ? (nowTick - playtimeAt) / 1000 : 0;
    return e.seconds + extra;
  };

  const toggleWater = async (p: Player, toWater: boolean) => {
    if (!isActive) return showToast('Mecz zakończony');
    // Optimistic local update so WODA/ŁAWKA persists immediately (and offline).
    setPlaytime(prev => ({
      ...prev,
      [p.player_id]: {
        seconds: prev[p.player_id]?.seconds || 0,
        on_water: toWater,
        stint_start: toWater ? new Date().toISOString() : null,
      },
    }));
    setPlaytimeAt(Date.now());
    try {
      const r = await api.recordSubstitution(matchId, p.player_id, toWater ? 'in' : 'out', state.settings?.Quarter || 1);
      if (!r?.queued) await loadPlaytime();
    } catch (e: any) {
      showToast(e.message || 'Błąd');
    }
  };

  const setStreamStartNow = async () => {
    if (!matchId || !youtube?.youtube_url) return;
    setStreamBusy(true);
    try {
      const res = await api.attachYouTube(matchId, youtube.youtube_url, { startNow: true });
      setState(prev => ({ ...prev, youtube: res }));
      showToast('Ustawiono start streamu');
    } catch (e: any) {
      showToast(e.message || 'Błąd');
    } finally {
      setStreamBusy(false);
    }
  };

  const openVideo = async (eventId: string) => {
    if (!matchId) return;
    try {
      const res = await api.getEventVideoUrl(matchId, eventId);
      if (res?.video_id != null) {
        setVideo({ video_id: res.video_id, seek_seconds: res.seek_seconds || 0 });
      } else {
        showToast('Brak znacznika wideo');
      }
    } catch {
      showToast('Brak znacznika wideo');
    }
  };

  const selectPlayer = (p: Player) => {
    if (!isActive) return;
    setState(prev => ({ ...prev, selected: p }));
  };

  const submitEvent = async (action: string) => {
    if (!state.selected) return showToast('Wybierz zawodnika');
    if (!isActive) return showToast('Mecz zakończony');

    const flags = getFlag(action, attackMode === 'man_up');

    try {
      const r = await api.createEvents([{
        player_id: state.selected.player_id,
        player_name: state.selected.name,
        note,
        ...flags,
      }]);
      setNote('');
      showToast(r?.queued ? 'Zapisano offline ⏳' : 'Zapisano');
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

  const undoLast = async () => {
    try {
      await api.undoEvent(5);
      showToast('Cofnięto ostatnią akcję');
      refreshEvents();
    } catch {
      showToast('Nic do cofnięcia');
    }
  };

  const Btn = ({ action, label }: { action: string; label: string }) => (
    <button className="btn" onClick={() => submitEvent(action)}>{label}</button>
  );

  const waterPlayers = state.rosterActive.filter(p => playtime[p.player_id]?.on_water);
  const benchPlayers = state.rosterActive.filter(p => !playtime[p.player_id]?.on_water);

  const PlayerCard = ({ p, inWater }: { p: Player; inWater: boolean }) => (
    <div
      className={`player${state.selected?.player_id === p.player_id ? ' active' : ''}${!isActive ? ' disabled' : ''}`}
      onClick={() => selectPlayer(p)}
    >
      <div className="num">{p.number}</div>
      <div className="name">{p.name}</div>
      <div className="player-meta">
        {inWater && <span className="player-time">{fmtTime(displaySeconds(p.player_id))}</span>}
        <button
          className={`sub-arrow${inWater ? ' sub-arrow--out' : ' sub-arrow--in'}`}
          onClick={e => { e.stopPropagation(); toggleWater(p, !inWater); }}
          title={inWater ? 'Zejście (na ławkę)' : 'Wejście (do wody)'}
          disabled={!isActive}
        >
          {inWater ? '▼' : '▲'}
        </button>
      </div>
    </div>
  );

  return (
    <div className="main-layout">
      {/* Player sidebar — WODA / ŁAWKA */}
      <div className="players-sidebar">
        {state.rosterActive.length === 0 ? (
          <div className="muted" style={{ padding: 12 }}>Brak składu</div>
        ) : (
          <>
            <div className="lineup-section">
              <div className="lineup-label lineup-label--water">WODA ({waterPlayers.length})</div>
              {waterPlayers.length === 0 && <div className="muted small" style={{ padding: '4px 8px' }}>—</div>}
              {waterPlayers.map(p => <PlayerCard key={p.player_id} p={p} inWater />)}
            </div>
            <div className="lineup-section">
              <div className="lineup-label">ŁAWKA ({benchPlayers.length})</div>
              {benchPlayers.map(p => <PlayerCard key={p.player_id} p={p} inWater={false} />)}
            </div>
          </>
        )}
      </div>

      {/* Actions */}
      <div className="actions-main">
        <div className="panel">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <div className="muted" style={{ flex: 1 }}>
              Wybrany: <span style={{ color: 'var(--accent)', fontWeight: 600 }}>
                {state.selected ? `#${state.selected.number} ${state.selected.name}` : '—'}
              </span>
            </div>
            {isActive && (
              <button className="btn small" onClick={undoLast} title="Cofnij ostatnią akcję">↶ Cofnij</button>
            )}
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

        {/* Stream bar */}
        {youtube?.youtube_url && (
          <div className="stream-bar">
            {streamSynced ? (
              <>
                <span style={{ color: 'var(--green)' }}>● Stream zsynchronizowany</span>
                <span className="muted small">— kliknij ▶ przy akcji, aby zobaczyć powtórkę</span>
                <button className="btn small" style={{ marginLeft: 'auto' }} onClick={setStreamStartNow} disabled={streamBusy}>
                  Ustaw start ponownie
                </button>
              </>
            ) : (
              <>
                <span className="muted">Stream podpięty, brak startu.</span>
                <button className="btn small primary" style={{ marginLeft: 'auto' }} onClick={setStreamStartNow} disabled={streamBusy}>
                  ▶ Ustaw start streamu = teraz
                </button>
              </>
            )}
          </div>
        )}

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
                  {streamSynced && (
                    <button
                      className="btn small event-video-btn"
                      onClick={() => openVideo(ev.id)}
                      title="Powtórka wideo"
                    >
                      ▶
                    </button>
                  )}
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

        {/* Voice notes */}
        {matchId && (
          <VoiceNotes
            matchId={matchId}
            showToast={showToast}
            canRecord={isActive}
            playerId={state.selected?.player_id}
          />
        )}
      </div>

      {video && (
        <VideoModal
          videoId={video.video_id}
          seekSeconds={video.seek_seconds}
          onClose={() => setVideo(null)}
        />
      )}
    </div>
  );
}
