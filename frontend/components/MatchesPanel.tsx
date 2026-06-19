'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { AppState, Match, AGE_CATEGORIES } from '@/lib/types';
import RosterEditor from '@/components/RosterEditor';

type Props = {
  state: AppState;
  showToast: (msg: string) => void;
  refresh: () => void;
};

export default function MatchesPanel({ state, showToast, refresh }: Props) {
  const [editMatch, setEditMatch] = useState<Match | null>(null);
  const [editForm, setEditForm] = useState({ date: '', opponent: '', place: '', ageCategory: '' });

  const [rosterMatch, setRosterMatch] = useState<Match | null>(null);
  const [rosterMap, setRosterMap] = useState<Map<string, number>>(new Map());
  const [rosterLoading, setRosterLoading] = useState(false);

  const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'ended'>('all');
  const [filterCat, setFilterCat] = useState<string>('all');

  const [streamMatch, setStreamMatch] = useState<Match | null>(null);
  const [streamUrl, setStreamUrl] = useState('');
  const [streamStart, setStreamStart] = useState<string | null>(null);
  const [streamLoading, setStreamLoading] = useState(false);

  const catNames = state.ageCategories.length
    ? state.ageCategories.map(c => c.name)
    : AGE_CATEGORIES;
  const activeMatchId = state.settings?.ActiveMatch;

  const openEdit = (m: Match) => {
    setEditForm({ date: m.date, opponent: m.opponent, place: m.place, ageCategory: m.ageCategory });
    setEditMatch(m);
  };

  const saveEdit = async () => {
    if (!editMatch) return;
    try {
      await api.editMatch(editMatch.match_id, editForm);
      setEditMatch(null);
      showToast('Zaktualizowano');
      refresh();
    } catch (e: any) {
      showToast(e.message || 'Błąd');
    }
  };

  const archive = async (matchId: string) => {
    if (!confirm('Zarchiwizować ten mecz?')) return;
    try {
      await api.archiveMatch(matchId);
      showToast('Zarchiwizowano');
      refresh();
    } catch (e: any) {
      showToast(e.message || 'Błąd');
    }
  };

  const setActive = async (matchId: string) => {
    try {
      await api.setActiveMatch(matchId);
      showToast('Ustawiono jako aktywny');
      refresh();
    } catch (e: any) {
      showToast(e.message || 'Błąd');
    }
  };

  const openRoster = async (m: Match) => {
    setRosterMatch(m);
    setRosterMap(new Map());
    setRosterLoading(true);
    try {
      const roster = await api.getRoster(m.match_id);
      const map = new Map<string, number>();
      roster.forEach((r: any) => map.set(r.player_id, r.number));
      setRosterMap(map);
    } catch {
      showToast('Błąd ładowania składu');
    } finally {
      setRosterLoading(false);
    }
  };

  const saveRoster = async () => {
    if (!rosterMatch) return;
    setRosterLoading(true);
    try {
      const roster = Array.from(rosterMap.entries()).map(([playerId, number]) => {
        const p = state.players.find(pl => pl.player_id === playerId);
        return { player_id: playerId, number, name: p?.name || '', team: 'my' };
      });
      await api.setRoster(rosterMatch.match_id, roster);
      setRosterMatch(null);
      showToast('Skład zapisany');
      refresh();
    } catch (e: any) {
      showToast(e.message || 'Błąd');
    } finally {
      setRosterLoading(false);
    }
  };

  const openStream = async (m: Match) => {
    setStreamMatch(m);
    setStreamUrl('');
    setStreamStart(null);
    setStreamLoading(true);
    try {
      const info = await api.getYouTube(m.match_id);
      if (info) {
        setStreamUrl(info.youtube_url || '');
        setStreamStart(info.stream_start_time || null);
      }
    } catch {
      // no stream yet
    } finally {
      setStreamLoading(false);
    }
  };

  const saveStreamLink = async () => {
    if (!streamMatch || !streamUrl.trim()) return showToast('Wklej link do transmisji');
    setStreamLoading(true);
    try {
      await api.attachYouTube(streamMatch.match_id, streamUrl.trim());
      showToast('Zapisano link');
      refresh();
    } catch (e: any) {
      showToast(e.message || 'Błąd');
    } finally {
      setStreamLoading(false);
    }
  };

  const setStreamStartNow = async () => {
    if (!streamMatch || !streamUrl.trim()) return showToast('Najpierw wklej link');
    setStreamLoading(true);
    try {
      const res = await api.attachYouTube(streamMatch.match_id, streamUrl.trim(), { startNow: true });
      setStreamStart(res.stream_start_time || null);
      showToast('Ustawiono start streamu');
      refresh();
    } catch (e: any) {
      showToast(e.message || 'Błąd');
    } finally {
      setStreamLoading(false);
    }
  };

  const filtered = state.matches.filter(m => {
    const okStatus = filterStatus === 'all' || m.status === filterStatus;
    const okCat = filterCat === 'all'
      || (filterCat === '' ? !m.ageCategory : m.ageCategory === filterCat);
    return okStatus && okCat;
  });

  return (
    <div className="wrap">
      <div className="card">
        <div className="subhead">Mecze ({filtered.length}{filtered.length !== state.matches.length ? ` z ${state.matches.length}` : ''})</div>

        <div className="matches-toolbar">
          <select value={filterStatus} onChange={e => setFilterStatus(e.target.value as any)}>
            <option value="all">Wszystkie statusy</option>
            <option value="active">Aktywne</option>
            <option value="ended">Zakończone</option>
          </select>
          <select value={filterCat} onChange={e => setFilterCat(e.target.value)}>
            <option value="all">Wszystkie kategorie</option>
            <option value="">Bez kategorii</option>
            {catNames.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {filtered.map(m => {
            const isActive = m.match_id === activeMatchId;
            return (
              <div key={m.match_id} className={`match-card${isActive ? ' match-card--active' : ''}`}>
                <div style={{ flex: 1, minWidth: 200 }}>
                  <div style={{ fontWeight: 600, fontSize: 15, display: 'flex', alignItems: 'center', gap: 8 }}>
                    vs {m.opponent || '—'}
                    {isActive && <span className="chip">aktywny</span>}
                  </div>
                  <div className="muted small">
                    {m.date || '—'} · {m.place || '—'} · {m.ageCategory || 'Bez kategorii'} · skład: {m.rosterCount ?? 0}
                  </div>
                </div>
                <span
                  className="tag"
                  style={{
                    borderColor: m.status === 'active' ? 'var(--green)' : 'var(--red)',
                    color: m.status === 'active' ? 'var(--green)' : 'var(--red)',
                    fontSize: 12,
                  }}
                >
                  {m.status === 'active' ? 'Aktywny' : 'Zakończony'}
                </span>
                <div className="match-card__actions">
                  {!isActive && <button className="btn small" onClick={() => setActive(m.match_id)}>Ustaw aktywny</button>}
                  <button className="btn small" onClick={() => openRoster(m)}>Skład</button>
                  <button className="btn small" onClick={() => openStream(m)}>Stream</button>
                  <button className="btn small" onClick={() => openEdit(m)}>Edytuj</button>
                  <button className="btn small danger" onClick={() => archive(m.match_id)}>Usuń</button>
                </div>
              </div>
            );
          })}
          {filtered.length === 0 && <div className="muted">Brak meczów</div>}
        </div>
      </div>

      {/* Edit metadata popup */}
      {editMatch && (
        <div className="popup-overlay" onClick={() => setEditMatch(null)}>
          <div className="popup" onClick={e => e.stopPropagation()}>
            <h3>Edytuj mecz</h3>
            <div className="form-group">
              <label>Data</label>
              <input type="date" value={editForm.date} onChange={e => setEditForm({ ...editForm, date: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Przeciwnik</label>
              <input value={editForm.opponent} onChange={e => setEditForm({ ...editForm, opponent: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Miejsce</label>
              <input value={editForm.place} onChange={e => setEditForm({ ...editForm, place: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Kategoria wiekowa</label>
              <select value={editForm.ageCategory} onChange={e => setEditForm({ ...editForm, ageCategory: e.target.value })}>
                <option value="">Bez kategorii</option>
                {catNames.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
              <button className="btn primary" onClick={saveEdit}>Zapisz</button>
              <button className="btn" onClick={() => setEditMatch(null)}>Anuluj</button>
            </div>
          </div>
        </div>
      )}

      {/* Edit roster popup */}
      {rosterMatch && (
        <div className="popup-overlay" onClick={() => setRosterMatch(null)}>
          <div className="popup popup--wide" onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <h3 style={{ margin: 0 }}>Skład — vs {rosterMatch.opponent || '—'}</h3>
              <button className="btn small" onClick={() => setRosterMatch(null)}>✕</button>
            </div>
            {rosterLoading && rosterMap.size === 0 ? (
              <div className="muted">Ładowanie...</div>
            ) : (
              <RosterEditor
                players={state.players}
                value={rosterMap}
                onChange={setRosterMap}
                filterCategory={rosterMatch.ageCategory}
              />
            )}
            <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
              <button className="btn primary" onClick={saveRoster} disabled={rosterLoading}>
                {rosterLoading ? 'Zapisywanie...' : 'Zapisz skład'}
              </button>
              <button className="btn" onClick={() => setRosterMatch(null)}>Anuluj</button>
            </div>
          </div>
        </div>
      )}

      {/* Stream popup */}
      {streamMatch && (
        <div className="popup-overlay" onClick={() => setStreamMatch(null)}>
          <div className="popup" onClick={e => e.stopPropagation()}>
            <h3>Transmisja — vs {streamMatch.opponent || '—'}</h3>
            <div className="form-group">
              <label>Link do transmisji (YouTube)</label>
              <input
                value={streamUrl}
                onChange={e => setStreamUrl(e.target.value)}
                placeholder="https://youtu.be/..."
              />
            </div>
            <div className="muted small" style={{ marginBottom: 12 }}>
              {streamStart
                ? `Start streamu ustawiony: ${new Date(streamStart + 'Z').toLocaleString('pl-PL')}`
                : 'Start streamu nieustawiony — kliknij „Ustaw start = teraz”, gdy transmisja ruszy.'}
            </div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <button className="btn primary" onClick={saveStreamLink} disabled={streamLoading}>Zapisz link</button>
              <button className="btn" onClick={setStreamStartNow} disabled={streamLoading}>Ustaw start = teraz</button>
              <button className="btn" onClick={() => setStreamMatch(null)} style={{ marginLeft: 'auto' }}>Zamknij</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
