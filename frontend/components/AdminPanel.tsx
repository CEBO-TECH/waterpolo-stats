'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { AppState, Player } from '@/lib/types';

type Props = {
  state: AppState;
  showToast: (msg: string) => void;
  refresh: () => void;
};

export default function AdminPanel({ state, showToast, refresh }: Props) {
  const [form, setForm] = useState({ date: '', opponent: '', place: '', ageCategory: 'Seniorzy' });
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<Map<string, number>>(new Map());
  const [loading, setLoading] = useState(false);

  const filteredPlayers = state.players.filter(p =>
    p.name.toLowerCase().includes(search.toLowerCase()) ||
    String(p.number).includes(search)
  );

  const togglePlayer = (p: Player) => {
    const next = new Map(selected);
    if (next.has(p.player_id)) {
      next.delete(p.player_id);
    } else {
      next.set(p.player_id, p.number);
    }
    setSelected(next);
  };

  const setPlayerNumber = (playerId: string, num: number) => {
    const next = new Map(selected);
    next.set(playerId, num);
    setSelected(next);
  };

  const copyPreviousRoster = async () => {
    const matchId = state.settings?.ActiveMatch;
    if (!matchId) return showToast('Brak aktywnego meczu');
    try {
      const roster = await api.getPreviousRoster(matchId);
      const next = new Map<string, number>();
      roster.forEach((r: any) => next.set(r.player_id, r.number));
      setSelected(next);
      showToast(`Skopiowano ${roster.length} zawodników`);
    } catch (e: any) {
      showToast('Brak poprzedniego meczu');
    }
  };

  const createMatch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.opponent.trim()) return showToast('Podaj przeciwnika');
    setLoading(true);
    try {
      const roster = Array.from(selected.entries()).map(([playerId, number]) => {
        const p = state.players.find(pl => pl.player_id === playerId);
        return { player_id: playerId, number, name: p?.name || '', team: 'my' };
      });

      await api.createMatch(form, roster);
      showToast('Mecz utworzony');
      setForm({ date: '', opponent: '', place: '', ageCategory: 'Seniorzy' });
      setSelected(new Map());
      refresh();
    } catch (e: any) {
      showToast(e.message || 'Błąd');
    } finally {
      setLoading(false);
    }
  };

  const selectedPlayers = state.players
    .filter(p => selected.has(p.player_id))
    .sort((a, b) => (selected.get(a.player_id) || 0) - (selected.get(b.player_id) || 0));

  return (
    <div className="wrap">
      <form onSubmit={createMatch}>
        <div className="card">
          <div className="subhead">Nowy mecz</div>
          <div className="form-row" style={{ marginBottom: 12 }}>
            <div>
              <label>Data</label>
              <input type="date" value={form.date} onChange={e => setForm({ ...form, date: e.target.value })} />
            </div>
            <div>
              <label>Przeciwnik</label>
              <input value={form.opponent} onChange={e => setForm({ ...form, opponent: e.target.value })} placeholder="Legia Warszawa" required />
            </div>
          </div>
          <div className="form-row" style={{ marginBottom: 12 }}>
            <div>
              <label>Miejsce</label>
              <input value={form.place} onChange={e => setForm({ ...form, place: e.target.value })} placeholder="Kraków" />
            </div>
            <div>
              <label>Kategoria</label>
              <select value={form.ageCategory} onChange={e => setForm({ ...form, ageCategory: e.target.value })}>
                <option>Seniorzy</option>
                <option>U19</option>
                <option>U17</option>
                <option>U15</option>
              </select>
            </div>
          </div>
        </div>

        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <div className="subhead" style={{ margin: 0 }}>Skład ({selected.size})</div>
            <button type="button" className="btn small" onClick={copyPreviousRoster}>
              Kopiuj z poprzedniego
            </button>
          </div>

          <input
            placeholder="Szukaj zawodnika..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{ marginBottom: 12 }}
          />

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 6, maxHeight: 300, overflowY: 'auto' }}>
            {filteredPlayers.map(p => (
              <div
                key={p.player_id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '8px 10px',
                  background: selected.has(p.player_id) ? 'rgba(76, 201, 240, 0.1)' : 'var(--bg)',
                  border: `1px solid ${selected.has(p.player_id) ? 'var(--accent)' : 'var(--border)'}`,
                  borderRadius: 'var(--radius-sm)',
                  cursor: 'pointer',
                }}
                onClick={() => togglePlayer(p)}
              >
                <input
                  type="checkbox"
                  checked={selected.has(p.player_id)}
                  onChange={() => {}}
                  style={{ width: 18, height: 18, accentColor: 'var(--accent)' }}
                />
                {selected.has(p.player_id) && (
                  <input
                    type="number"
                    value={selected.get(p.player_id) || ''}
                    onClick={e => e.stopPropagation()}
                    onChange={e => setPlayerNumber(p.player_id, Number(e.target.value))}
                    style={{ width: 48, padding: '4px 6px', textAlign: 'center', fontSize: 14 }}
                    min={0}
                    max={99}
                  />
                )}
                <span style={{ fontSize: 14 }}>{p.name}</span>
              </div>
            ))}
          </div>
        </div>

        {selectedPlayers.length > 0 && (
          <div className="card">
            <div className="subhead">Podgląd składu</div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {selectedPlayers.map(p => (
                <span key={p.player_id} className="tag">
                  #{selected.get(p.player_id)} {p.name}
                </span>
              ))}
            </div>
          </div>
        )}

        <button type="submit" className="btn primary" disabled={loading} style={{ width: '100%' }}>
          {loading ? 'Tworzenie...' : 'Utwórz mecz'}
        </button>
      </form>
    </div>
  );
}
