'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { AppState, Match } from '@/lib/types';

type Props = {
  state: AppState;
  showToast: (msg: string) => void;
  refresh: () => void;
};

export default function MatchesPanel({ state, showToast, refresh }: Props) {
  const [editMatch, setEditMatch] = useState<Match | null>(null);
  const [editForm, setEditForm] = useState({ date: '', opponent: '', place: '', ageCategory: 'Seniorzy' });

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

  return (
    <div className="wrap">
      <div className="card">
        <div className="subhead">Mecze ({state.matches.length})</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {state.matches.map(m => (
            <div
              key={m.match_id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '12px 14px',
                background: 'var(--bg)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-sm)',
                flexWrap: 'wrap',
              }}
            >
              <div style={{ flex: 1, minWidth: 200 }}>
                <div style={{ fontWeight: 600, fontSize: 15 }}>
                  vs {m.opponent || '—'}
                </div>
                <div className="muted small">
                  {m.date} · {m.place} · {m.ageCategory}
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
              <button className="btn small" onClick={() => openEdit(m)}>Edytuj</button>
              <button className="btn small danger" onClick={() => archive(m.match_id)}>Usuń</button>
            </div>
          ))}
          {state.matches.length === 0 && <div className="muted">Brak meczów</div>}
        </div>
      </div>

      {/* Edit popup */}
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
                <option>Seniorzy</option>
                <option>U19</option>
                <option>U17</option>
                <option>U15</option>
              </select>
            </div>
            <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
              <button className="btn primary" onClick={saveEdit}>Zapisz</button>
              <button className="btn" onClick={() => setEditMatch(null)}>Anuluj</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
