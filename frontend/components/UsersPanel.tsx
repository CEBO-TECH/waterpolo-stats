'use client';

import { useEffect, useState, useCallback } from 'react';
import { api } from '@/lib/api';
import { AppState } from '@/lib/types';

const ROLE_LABELS: Record<string, string> = {
  owner: 'Właściciel',
  coach: 'Trener',
  player: 'Zawodnik',
};

type Props = { state: AppState; showToast: (m: string) => void };

export default function UsersPanel({ state, showToast }: Props) {
  const isOwner = state.user?.role === 'owner';
  const [members, setMembers] = useState<any[]>([]);
  const [invitations, setInvitations] = useState<any[]>([]);
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('player');
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    try {
      setMembers(await api.getMembers());
      if (isOwner) setInvitations(await api.getInvitations());
    } catch (e: any) {
      showToast(e.message || 'Błąd');
    }
  }, [isOwner, showToast]);

  useEffect(() => { load(); }, [load]);

  const invite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return showToast('Podaj email');
    setLoading(true);
    try {
      const r = await api.inviteMember(email.trim(), role);
      if (r.added) {
        showToast('Dodano do klubu');
      } else {
        showToast('Zaproszenie utworzone — dołączy po rejestracji tym e-mailem');
      }
      setEmail('');
      load();
    } catch (e: any) {
      showToast(e.message || 'Błąd');
    } finally {
      setLoading(false);
    }
  };

  const changeRole = async (userId: string, newRole: string) => {
    try { await api.updateMemberRole(userId, newRole); showToast('Zmieniono rolę'); load(); }
    catch (e: any) { showToast(e.message || 'Błąd'); }
  };

  const remove = async (userId: string, em: string) => {
    if (!confirm(`Usunąć ${em} z klubu?`)) return;
    try { await api.removeMember(userId); showToast('Usunięto'); load(); }
    catch (e: any) { showToast(e.message || 'Błąd'); }
  };

  const revoke = async (id: string) => {
    try { await api.revokeInvitation(id); showToast('Cofnięto zaproszenie'); load(); }
    catch (e: any) { showToast(e.message || 'Błąd'); }
  };

  return (
    <div className="wrap">
      <div className="card">
        <div className="subhead">Członkowie klubu ({members.length})</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {members.map(m => (
            <div key={m.user_id} className="player-row">
              <div className="player-row__info">
                <span className="player-row__name">{m.email}</span>
              </div>
              {isOwner ? (
                <select
                  className="players-toolbar__select"
                  value={m.role}
                  onChange={e => changeRole(m.user_id, e.target.value)}
                  style={{ minHeight: 36, flex: '0 0 140px' }}
                >
                  <option value="owner">Właściciel</option>
                  <option value="coach">Trener</option>
                  <option value="player">Zawodnik</option>
                </select>
              ) : (
                <span className="chip">{ROLE_LABELS[m.role] || m.role}</span>
              )}
              {isOwner && (
                <button className="btn small danger" onClick={() => remove(m.user_id, m.email)}>Usuń</button>
              )}
            </div>
          ))}
          {members.length === 0 && <div className="muted">Brak członków</div>}
        </div>
      </div>

      {isOwner && (
        <div className="card">
          <div className="subhead">Zaproś użytkownika</div>
          <form onSubmit={invite}>
            <div className="form-row" style={{ marginBottom: 12 }}>
              <div style={{ flex: 3 }}>
                <label>Email</label>
                <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="zawodnik@klub.pl" />
              </div>
              <div>
                <label>Rola</label>
                <select value={role} onChange={e => setRole(e.target.value)}>
                  <option value="player">Zawodnik</option>
                  <option value="coach">Trener</option>
                </select>
              </div>
            </div>
            <button type="submit" className="btn primary" disabled={loading}>Zaproś</button>
          </form>
          <div className="muted small" style={{ marginTop: 10 }}>
            Bez linków i kodów — zaproszona osoba po prostu rejestruje się tym samym adresem
            e-mail i automatycznie dołącza do klubu z przypisaną rolą.
          </div>
        </div>
      )}

      {isOwner && invitations.length > 0 && (
        <div className="card">
          <div className="subhead">Oczekujące zaproszenia ({invitations.length})</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {invitations.map(i => (
              <div key={i.id} className="player-row">
                <div className="player-row__info">
                  <span className="player-row__name">{i.email}</span>
                  <div className="chip-row"><span className="chip">{ROLE_LABELS[i.role] || i.role}</span></div>
                </div>
                <span className="muted small">dołączy po rejestracji</span>
                <button className="btn small danger" onClick={() => revoke(i.id)}>Cofnij</button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
