'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { ClubInfo } from '@/lib/types';

type Props = {
  onLogin: () => void;
};

type Step = 'auth' | 'pick-club' | 'create-club' | 'no-club';

const ROLE_LABELS: Record<string, string> = {
  owner: 'Właściciel',
  coach: 'Trener',
  player: 'Zawodnik',
};

export default function LoginPage({ onLogin }: Props) {
  const [isRegister, setIsRegister] = useState(false);
  const [step, setStep] = useState<Step>('auth');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [clubName, setClubName] = useState('');
  const [clubs, setClubs] = useState<ClubInfo[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const fail = (e: any) => setError(e?.message || 'Wystąpił błąd');

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (isRegister) {
        // Register only creates the account. Club membership is granted by email:
        // if this address was invited or attached to a player, the backend auto-joins.
        await api.register(email, password);
        await api.login(email, password);
        const me = await api.getMe();
        const userClubs: ClubInfo[] = me.clubs || [];
        if (userClubs.length === 0) {
          setStep('no-club');
        } else if (userClubs.length === 1) {
          await api.selectClub(userClubs[0].club_id);
          onLogin();
        } else {
          setClubs(userClubs);
          setStep('pick-club');
        }
        return;
      }

      await api.login(email, password);
      const me = await api.getMe();
      const userClubs: ClubInfo[] = me.clubs || [];

      if (userClubs.length === 0) {
        setStep('create-club');
      } else if (userClubs.length === 1) {
        await api.selectClub(userClubs[0].club_id);
        onLogin();
      } else {
        setClubs(userClubs);
        setStep('pick-club');
      }
    } catch (err: any) {
      fail(err);
    } finally {
      setLoading(false);
    }
  };

  const pickClub = async (clubId: string) => {
    setError('');
    setLoading(true);
    try {
      await api.selectClub(clubId);
      onLogin();
    } catch (err: any) {
      fail(err);
    } finally {
      setLoading(false);
    }
  };

  const createClubAndEnter = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const club = await api.createClub(clubName.trim());
      await api.selectClub(club.id);
      onLogin();
    } catch (err: any) {
      fail(err);
    } finally {
      setLoading(false);
    }
  };

  // ─── Club picker (user belongs to multiple clubs) ───
  if (step === 'pick-club') {
    return (
      <div className="login-page">
        <div className="login-card">
          <h1>Wybierz klub</h1>
          <p className="subtitle">Należysz do kilku klubów</p>
          {error && <div className="login-error">{error}</div>}
          <div className="club-list">
            {clubs.map(c => (
              <button
                key={c.club_id}
                type="button"
                className="club-card"
                onClick={() => pickClub(c.club_id)}
                disabled={loading}
              >
                <span className="club-card__name">{c.club_name}</span>
                <span className="muted small">{ROLE_LABELS[c.role] || c.role}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // ─── Create first club (logged-in user has no club yet) ───
  if (step === 'create-club') {
    return (
      <div className="login-page">
        <form className="login-card" onSubmit={createClubAndEnter}>
          <h1>Utwórz klub</h1>
          <p className="subtitle">Nie należysz jeszcze do żadnego klubu</p>
          {error && <div className="login-error">{error}</div>}
          <div className="form-group">
            <label>Nazwa klubu</label>
            <input
              type="text"
              value={clubName}
              onChange={e => setClubName(e.target.value)}
              placeholder="KS Waterpolo Kraków"
              required
              autoFocus
            />
          </div>
          <button type="submit" className="btn primary" disabled={loading} style={{ width: '100%', marginTop: 8 }}>
            {loading ? 'Tworzenie...' : 'Utwórz i wejdź'}
          </button>
        </form>
      </div>
    );
  }

  // ─── Account created, but email not yet attached to any club ───
  if (step === 'no-club') {
    return (
      <div className="login-page">
        <div className="login-card">
          <h1>Konto utworzone 🎉</h1>
          <p className="subtitle">Nie należysz jeszcze do żadnego klubu</p>
          <p className="muted" style={{ textAlign: 'center', lineHeight: 1.5 }}>
            Twój adres <strong>{email}</strong> nie jest przypisany do żadnego klubu.
            Poproś trenera lub właściciela, aby dodał Cię tym adresem e-mail — po ponownym
            zalogowaniu dołączysz automatycznie.
          </p>
          <button
            className="btn primary"
            onClick={() => { setIsRegister(false); setStep('auth'); setError(''); }}
            style={{ width: '100%', marginTop: 16 }}
          >
            Wróć do logowania
          </button>
        </div>
      </div>
    );
  }

  // ─── Login / Register ───
  return (
    <div className="login-page">
      <form className="login-card" onSubmit={handleAuth}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img className="login-logo" src="/logo.png" alt="Cap Track" width={84} height={84} />
        <h1>Cap Track</h1>
        <p className="subtitle">
          {isRegister ? 'Utwórz konto' : 'Zaloguj się do platformy'}
        </p>

        {error && <div className="login-error">{error}</div>}

        <div className="form-group">
          <label>Email</label>
          <input
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            placeholder="trener@klub.pl"
            required
          />
        </div>

        <div className="form-group">
          <label>Hasło</label>
          <input
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder="••••••••"
            required
          />
        </div>

        {isRegister && (
          <p className="muted small text-center" style={{ marginTop: -4, marginBottom: 4 }}>
            Po rejestracji dołączysz do klubu automatycznie, jeśli trener dodał Twój adres e-mail.
          </p>
        )}

        <button
          type="submit"
          className="btn primary"
          disabled={loading}
          style={{ width: '100%', marginTop: 8 }}
        >
          {loading ? 'Ładowanie...' : isRegister ? 'Utwórz konto' : 'Zaloguj'}
        </button>

        <p className="muted text-center" style={{ marginTop: 16 }}>
          {isRegister ? 'Masz już konto?' : 'Nie masz konta?'}{' '}
          <span
            style={{ color: 'var(--accent)', cursor: 'pointer' }}
            onClick={() => { setIsRegister(!isRegister); setError(''); }}
          >
            {isRegister ? 'Zaloguj się' : 'Zarejestruj'}
          </span>
        </p>
      </form>
    </div>
  );
}
