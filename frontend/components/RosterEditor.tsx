'use client';

import { useState } from 'react';
import { Player } from '@/lib/types';

type Props = {
  players: Player[];
  value: Map<string, number>;
  onChange: (next: Map<string, number>) => void;
  /** When set (and no search query), narrow the picker to this category. */
  filterCategory?: string;
};

/**
 * Reusable squad picker — search across all players, optional category narrowing,
 * checkbox + jersey number, live preview. Controlled via value/onChange.
 */
export default function RosterEditor({ players, value, onChange, filterCategory }: Props) {
  const [search, setSearch] = useState('');

  const togglePlayer = (p: Player) => {
    const next = new Map(value);
    if (next.has(p.player_id)) next.delete(p.player_id);
    else next.set(p.player_id, p.number);
    onChange(next);
  };

  const setPlayerNumber = (playerId: string, num: number) => {
    const next = new Map(value);
    next.set(playerId, num);
    onChange(next);
  };

  const inCategory = (p: Player) =>
    !filterCategory || (p.age_categories || []).includes(filterCategory);

  const filtered = players.filter(p => {
    const q = search.trim().toLowerCase();
    if (q) return p.name.toLowerCase().includes(q) || String(p.number).includes(q);
    return inCategory(p);
  });

  const selectedPlayers = players
    .filter(p => value.has(p.player_id))
    .sort((a, b) => (value.get(a.player_id) || 0) - (value.get(b.player_id) || 0));

  return (
    <>
      <input
        placeholder="Szukaj zawodnika (wszyscy)..."
        value={search}
        onChange={e => setSearch(e.target.value)}
        style={{ marginBottom: 12 }}
      />

      <div className="roster-grid">
        {filtered.map(p => {
          const on = value.has(p.player_id);
          return (
            <div
              key={p.player_id}
              className={`roster-pick${on ? ' roster-pick--on' : ''}`}
              onClick={() => togglePlayer(p)}
            >
              <input
                type="checkbox"
                checked={on}
                onChange={() => {}}
                style={{ width: 18, height: 18, accentColor: 'var(--accent)' }}
              />
              {on && (
                <input
                  type="number"
                  value={value.get(p.player_id) || ''}
                  onClick={e => e.stopPropagation()}
                  onChange={e => setPlayerNumber(p.player_id, Number(e.target.value))}
                  style={{ width: 48, padding: '4px 6px', textAlign: 'center', fontSize: 14 }}
                  min={0}
                  max={99}
                />
              )}
              <span style={{ fontSize: 14, flex: 1 }}>{p.name}</span>
              {(p.age_categories || []).length > 0 && (
                <span className="chip-row">
                  {(p.age_categories || []).map(c => <span key={c} className="chip">{c}</span>)}
                </span>
              )}
            </div>
          );
        })}
        {filtered.length === 0 && <div className="muted">Brak zawodników</div>}
      </div>

      {selectedPlayers.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <div className="muted small" style={{ marginBottom: 6 }}>Podgląd składu ({selectedPlayers.length})</div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {selectedPlayers.map(p => (
              <span key={p.player_id} className="tag">#{value.get(p.player_id)} {p.name}</span>
            ))}
          </div>
        </div>
      )}
    </>
  );
}
