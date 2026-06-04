'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { AppState } from '@/lib/types';

type Props = {
  state: AppState;
  showToast: (msg: string) => void;
  refresh: () => void;
};

export default function PlayersPanel({ state, showToast, refresh }: Props) {
  const [number, setNumber] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);

  const addPlayer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return showToast('Podaj imię zawodnika');
    setLoading(true);
    try {
      await api.createPlayer(Number(number) || 0, name.trim());
      setNumber('');
      setName('');
      showToast('Dodano zawodnika');
      refresh();
    } catch (e: any) {
      showToast(e.message || 'Błąd');
    } finally {
      setLoading(false);
    }
  };

  const deletePlayer = async (playerId: string, playerName: string) => {
    if (!confirm(`Usunąć ${playerName}? Wszystkie statystyki zostaną skasowane.`)) return;
    try {
      await api.deletePlayer(playerId);
      showToast('Usunięto');
      refresh();
    } catch (e: any) {
      showToast(e.message || 'Błąd');
    }
  };

  return (
    <div className="wrap">
      <div className="card">
        <div className="subhead">Dodaj zawodnika</div>
        <form onSubmit={addPlayer}>
          <div className="form-row" style={{ marginBottom: 12 }}>
            <div>
              <label>Numer</label>
              <input
                type="number"
                value={number}
                onChange={e => setNumber(e.target.value)}
                placeholder="3"
                style={{ width: 80 }}
              />
            </div>
            <div style={{ flex: 3 }}>
              <label>Imię i nazwisko</label>
              <input
                value={name}
                onChange={e => setName(e.target.value)}
                placeholder="Jan Kowalski"
              />
            </div>
          </div>
          <button type="submit" className="btn primary" disabled={loading}>
            Dodaj
          </button>
        </form>
      </div>

      <div className="card">
        <div className="subhead">Zawodnicy ({state.players.length})</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 8 }}>
          {state.players.map(p => (
            <div
              key={p.player_id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '10px 12px',
                background: 'var(--bg)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-sm)',
              }}
            >
              <span style={{ fontSize: 20, fontWeight: 700, color: 'var(--accent)', minWidth: 36, textAlign: 'center' }}>
                {p.number}
              </span>
              <span style={{ flex: 1, fontSize: 14 }}>{p.name}</span>
              <button className="btn small danger" onClick={() => deletePlayer(p.player_id, p.name)}>
                ✕
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
