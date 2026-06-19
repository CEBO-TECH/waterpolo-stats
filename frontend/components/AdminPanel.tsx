'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { AppState, AGE_CATEGORIES } from '@/lib/types';
import RosterEditor from '@/components/RosterEditor';

type Props = {
  state: AppState;
  showToast: (msg: string) => void;
  refresh: () => void;
};

export default function AdminPanel({ state, showToast, refresh }: Props) {
  const [form, setForm] = useState({ date: '', opponent: '', place: '', ageCategory: '' });
  const [selected, setSelected] = useState<Map<string, number>>(new Map());
  const [loading, setLoading] = useState(false);

  const catNames = state.ageCategories.length
    ? state.ageCategories.map(c => c.name)
    : AGE_CATEGORIES;

  // Picking a category pre-fills the squad with players from that group.
  const onCategoryChange = (cat: string) => {
    setForm({ ...form, ageCategory: cat });
    if (cat) {
      const next = new Map<string, number>();
      state.players
        .filter(p => (p.age_categories || []).includes(cat))
        .forEach(p => next.set(p.player_id, p.number));
      setSelected(next);
    } else {
      setSelected(new Map());
    }
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
    } catch {
      showToast('Brak poprzedniego meczu');
    }
  };

  const doCreate = async (rosterMap: Map<string, number>) => {
    if (!form.opponent.trim()) return showToast('Podaj przeciwnika');
    setLoading(true);
    try {
      const roster = Array.from(rosterMap.entries()).map(([playerId, number]) => {
        const p = state.players.find(pl => pl.player_id === playerId);
        return { player_id: playerId, number, name: p?.name || '', team: 'my' };
      });
      await api.createMatch(form, roster);
      showToast(roster.length ? 'Mecz utworzony' : 'Mecz utworzony — skład dodasz później');
      setForm({ date: '', opponent: '', place: '', ageCategory: '' });
      setSelected(new Map());
      refresh();
    } catch (e: any) {
      showToast(e.message || 'Błąd');
    } finally {
      setLoading(false);
    }
  };

  const createMatch = (e: React.FormEvent) => {
    e.preventDefault();
    doCreate(selected);
  };

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
              <select value={form.ageCategory} onChange={e => onCategoryChange(e.target.value)}>
                <option value="">Bez kategorii</option>
                {catNames.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          </div>
        </div>

        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
            <div className="subhead" style={{ margin: 0 }}>Skład ({selected.size})</div>
            <button type="button" className="btn small" onClick={copyPreviousRoster}>
              Kopiuj z poprzedniego
            </button>
          </div>
          <div className="muted small" style={{ marginBottom: 12 }}>
            {form.ageCategory
              ? `Lista zawęża się do kategorii „${form.ageCategory}” — wpisz w wyszukiwarce, aby dodać kogoś spoza grupy.`
              : 'Wybierz kategorię powyżej, aby automatycznie podpowiedzieć skład — lub utwórz mecz bez składu i dodaj go później.'}
          </div>

          <RosterEditor
            players={state.players}
            value={selected}
            onChange={setSelected}
            filterCategory={form.ageCategory}
          />
        </div>

        <div style={{ display: 'flex', gap: 8 }}>
          <button type="submit" className="btn primary" disabled={loading} style={{ flex: 1 }}>
            {loading ? 'Tworzenie...' : 'Utwórz mecz'}
          </button>
          <button type="button" className="btn" disabled={loading} onClick={() => doCreate(new Map())}>
            Utwórz bez składu
          </button>
        </div>
      </form>
    </div>
  );
}
