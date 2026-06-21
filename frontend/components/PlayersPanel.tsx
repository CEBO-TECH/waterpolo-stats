'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { AppState, Player, AGE_CATEGORIES } from '@/lib/types';
import PlayerProfile from '@/components/PlayerProfile';

type Props = {
  state: AppState;
  showToast: (msg: string) => void;
  refresh: () => void;
};

type SortKey = 'number' | 'name';

export default function PlayersPanel({ state, showToast, refresh }: Props) {
  const [name, setName] = useState('');
  const [birthYear, setBirthYear] = useState('');
  const [playerEmail, setPlayerEmail] = useState('');
  const [loading, setLoading] = useState(false);

  const [search, setSearch] = useState('');
  const [sort, setSort] = useState<SortKey>('name');
  const [filterCat, setFilterCat] = useState<string>('all');

  const [editing, setEditing] = useState<Player | null>(null);
  const [editForm, setEditForm] = useState({ name: '', team: 'my', birthYear: '', email: '' });
  const [editCats, setEditCats] = useState<string[]>([]);
  const [editLoading, setEditLoading] = useState(false);

  const [profile, setProfile] = useState<Player | null>(null);

  const [newCat, setNewCat] = useState('');

  const catNames = state.ageCategories.length
    ? state.ageCategories.map(c => c.name)
    : AGE_CATEGORIES;
  const canManage = state.user?.role === 'owner' || state.user?.role === 'coach';

  const addCategory = async () => {
    if (!newCat.trim()) return;
    try {
      await api.createAgeCategory(newCat.trim());
      setNewCat('');
      showToast('Dodano kategorię');
      refresh();
    } catch (e: any) {
      showToast(e.message || 'Błąd');
    }
  };

  const removeCategory = async (id: string, catName: string) => {
    if (!confirm(`Usunąć kategorię „${catName}”? Przypisania zawodników pozostaną.`)) return;
    try {
      await api.deleteAgeCategory(id);
      showToast('Usunięto kategorię');
      refresh();
    } catch (e: any) {
      showToast(e.message || 'Błąd');
    }
  };

  const addPlayer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return showToast('Podaj imię zawodnika');
    setLoading(true);
    try {
      await api.createPlayer(name.trim(), {
        birth_year: birthYear ? Number(birthYear) : null,
        email: playerEmail.trim() || null,
      });
      setName('');
      setBirthYear('');
      setPlayerEmail('');
      showToast('Dodano zawodnika');
      refresh();
    } catch (e: any) {
      showToast(e.message || 'Błąd');
    } finally {
      setLoading(false);
    }
  };

  const invitePlayer = async (email: string) => {
    try {
      const r = await api.inviteMember(email, 'player');
      if (r.added) {
        showToast('Dodano konto do klubu');
      } else {
        const link = `${window.location.origin}/?invite=${r.invitation.token}`;
        navigator.clipboard?.writeText(link);
        showToast('Link zaproszenia skopiowany');
      }
      refresh();
    } catch (e: any) {
      showToast(e.message || 'Błąd');
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

  const openEdit = (p: Player) => {
    setEditForm({
      name: p.name, team: p.team || 'my',
      birthYear: p.birth_year ? String(p.birth_year) : '', email: p.email || '',
    });
    setEditCats(p.age_categories || []);
    setEditing(p);
  };

  const toggleEditCat = (cat: string) => {
    setEditCats(prev => prev.includes(cat) ? prev.filter(c => c !== cat) : [...prev, cat]);
  };

  const saveEdit = async () => {
    if (!editing) return;
    if (!editForm.name.trim()) return showToast('Podaj imię zawodnika');
    setEditLoading(true);
    try {
      await api.updatePlayer(editing.player_id, {
        name: editForm.name.trim(),
        team: editForm.team,
        birth_year: editForm.birthYear ? Number(editForm.birthYear) : null,
        email: editForm.email.trim() || null,
      });
      await api.setPlayerAgeCategories(editing.player_id, editCats);
      setEditing(null);
      showToast('Zapisano');
      refresh();
    } catch (e: any) {
      showToast(e.message || 'Błąd');
    } finally {
      setEditLoading(false);
    }
  };

  const filtered = state.players
    .filter(p => {
      const q = search.toLowerCase();
      const matchesSearch = !q || p.name.toLowerCase().includes(q) || String(p.number).includes(q);
      const matchesCat = filterCat === 'all' || (p.age_categories || []).includes(filterCat);
      return matchesSearch && matchesCat;
    })
    .sort((a, b) => sort === 'number'
      ? a.number - b.number
      : a.name.localeCompare(b.name, 'pl'));

  return (
    <div className="wrap">
      {/* Add player */}
      <div className="card">
        <div className="subhead">Dodaj zawodnika</div>
        <form onSubmit={addPlayer}>
          <div className="form-row" style={{ marginBottom: 12 }}>
            <div style={{ flex: 3 }}>
              <label>Imię i nazwisko</label>
              <input value={name} onChange={e => setName(e.target.value)} placeholder="Jan Kowalski" />
            </div>
            <div>
              <label>Rocznik</label>
              <input type="number" value={birthYear} onChange={e => setBirthYear(e.target.value)} placeholder="2010" style={{ width: 100 }} />
            </div>
          </div>
          <div className="muted small" style={{ marginBottom: 12 }}>
            Numer na czepku nadajesz przy tworzeniu składu na mecz.
          </div>
          <div className="form-row" style={{ marginBottom: 12 }}>
            <div style={{ flex: 1 }}>
              <label>Email (opcjonalnie — do konta zawodnika)</label>
              <input type="email" value={playerEmail} onChange={e => setPlayerEmail(e.target.value)} placeholder="zawodnik@klub.pl" />
            </div>
          </div>
          <button type="submit" className="btn primary" disabled={loading}>Dodaj</button>
        </form>
      </div>

      {/* Age category dictionary (club-wide) */}
      {canManage && (
        <div className="card">
          <div className="subhead">Kategorie wiekowe klubu</div>
          <div className="chip-row" style={{ marginBottom: 12 }}>
            {state.ageCategories.length === 0 ? (
              <span className="muted small">Brak kategorii — dodaj pierwszą</span>
            ) : (
              state.ageCategories.map(cat => (
                <span key={cat.id} className="chip chip--removable">
                  {cat.name}
                  <button
                    className="chip__remove"
                    onClick={() => removeCategory(cat.id, cat.name)}
                    aria-label={`Usuń ${cat.name}`}
                  >
                    ✕
                  </button>
                </span>
              ))
            )}
          </div>
          <div className="form-row">
            <input
              value={newCat}
              onChange={e => setNewCat(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addCategory(); } }}
              placeholder="Nowa kategoria (np. U13)"
            />
            <button type="button" className="btn" onClick={addCategory} style={{ flex: '0 0 auto' }}>
              Dodaj kategorię
            </button>
          </div>
        </div>
      )}

      {/* Toolbar */}
      <div className="card">
        <div className="players-toolbar">
          <input
            className="players-toolbar__search"
            placeholder="Szukaj zawodnika..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
          <select value={filterCat} onChange={e => setFilterCat(e.target.value)} className="players-toolbar__select">
            <option value="all">Wszystkie kategorie</option>
            {catNames.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <div className="toggle-switch">
            <div className={`toggle-option${sort === 'number' ? ' active' : ''}`} onClick={() => setSort('number')}>Nr</div>
            <div className={`toggle-option${sort === 'name' ? ' active' : ''}`} onClick={() => setSort('name')}>A-Z</div>
          </div>
        </div>

        <div className="subhead" style={{ marginTop: 12 }}>
          Zawodnicy ({filtered.length}{filtered.length !== state.players.length ? ` z ${state.players.length}` : ''})
        </div>

        <div className="players-grid">
          {filtered.map(p => (
            <div key={p.player_id} className="player-row">
              {p.number ? <span className="player-row__num">{p.number}</span> : null}
              <div className="player-row__info">
                <span className="player-row__name">
                  {p.name}
                  {p.birth_year ? <span className="muted small"> · {p.birth_year}</span> : null}
                </span>
                <div className="chip-row">
                  {(p.age_categories || []).length === 0 ? (
                    <span className="muted small">bez kategorii</span>
                  ) : (
                    (p.age_categories || []).map(c => <span key={c} className="chip">{c}</span>)
                  )}
                  {p.has_account && <span className="chip" style={{ color: 'var(--green)' }}>✓ konto</span>}
                </div>
              </div>
              <div className="player-row__actions">
                {canManage && p.email && !p.has_account && (
                  <button className="btn small" onClick={() => invitePlayer(p.email!)}>Zaproś</button>
                )}
                <button className="btn small" onClick={() => setProfile(p)}>Profil</button>
                <button className="btn small" onClick={() => openEdit(p)}>Edytuj</button>
                <button className="btn small danger" onClick={() => deletePlayer(p.player_id, p.name)}>✕</button>
              </div>
            </div>
          ))}
          {filtered.length === 0 && <div className="muted">Brak zawodników</div>}
        </div>
      </div>

      {/* Edit popup */}
      {editing && (
        <div className="popup-overlay" onClick={() => setEditing(null)}>
          <div className="popup" onClick={e => e.stopPropagation()}>
            <h3>Edytuj zawodnika</h3>
            <div className="form-row" style={{ marginBottom: 12 }}>
              <div style={{ flex: 3 }}>
                <label>Imię i nazwisko</label>
                <input value={editForm.name} onChange={e => setEditForm({ ...editForm, name: e.target.value })} />
              </div>
              <div>
                <label>Rocznik</label>
                <input type="number" value={editForm.birthYear} onChange={e => setEditForm({ ...editForm, birthYear: e.target.value })} placeholder="2010" style={{ width: 100 }} />
              </div>
            </div>
            <div className="form-row" style={{ marginBottom: 12 }}>
              <div style={{ flex: 2 }}>
                <label>Email (konto zawodnika)</label>
                <input type="email" value={editForm.email} onChange={e => setEditForm({ ...editForm, email: e.target.value })} placeholder="zawodnik@klub.pl" />
              </div>
              <div style={{ flex: 1 }}>
                <label>Drużyna</label>
                <select value={editForm.team} onChange={e => setEditForm({ ...editForm, team: e.target.value })}>
                  <option value="my">Moja drużyna</option>
                  <option value="opponent">Przeciwnik</option>
                </select>
              </div>
            </div>
            <div className="form-group">
              <label>Kategorie wiekowe</label>
              <div className="chip-row">
                {catNames.map(c => (
                  <button
                    key={c}
                    type="button"
                    className={`chip chip--toggle${editCats.includes(c) ? ' chip--on' : ''}`}
                    onClick={() => toggleEditCat(c)}
                  >
                    {c}
                  </button>
                ))}
              </div>
            </div>
            <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
              <button className="btn primary" onClick={saveEdit} disabled={editLoading}>
                {editLoading ? 'Zapisywanie...' : 'Zapisz'}
              </button>
              <button className="btn" onClick={() => setEditing(null)}>Anuluj</button>
            </div>
          </div>
        </div>
      )}

      {/* Profile popup */}
      {profile && (
        <PlayerProfile
          playerId={profile.player_id}
          playerLabel={profile.number ? `#${profile.number} ${profile.name}` : profile.name}
          onClose={() => setProfile(null)}
        />
      )}
    </div>
  );
}
