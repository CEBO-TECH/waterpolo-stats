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
  const [inviteLink, setInviteLink] = useState<string | null>(null);
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
        setInviteLink(null);
      } else {
        setInviteLink(`${window.location.origin}/?invite=${r.invitation.token}`);
        showToast('Utworzono zaproszenie');
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

  const copy = (link: string) => {
    navigator.clipboard?.writeText(link);
    showToast('Skopiowano link');
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
          {inviteLink && (
            <div style={{ marginTop: 12 }}>
              <div className="muted small" style={{ marginBottom: 4 }}>
                Konto nie istnieje — przekaż link zaproszenia (przyjmuje się po zalogowaniu na ten email):
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <input readOnly value={inviteLink} onClick={e => (e.target as HTMLInputElement).select()} />
                <button type="button" className="btn" onClick={() => copy(inviteLink)} style={{ flex: '0 0 auto' }}>Kopiuj</button>
              </div>
            </div>
          )}
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
                <button className="btn small" onClick={() => copy(`${window.location.origin}/?invite=${i.token}`)}>Kopiuj link</button>
                <button className="btn small danger" onClick={() => revoke(i.id)}>Cofnij</button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
