'use client';

import { useState } from 'react';
import { api } from '@/lib/api';

type Props = {
  onLogin: () => void;
};

export default function LoginPage({ onLogin }: Props) {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [clubName, setClubName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isRegister) {
        await api.register(email, password);
        await api.login(email, password);
        if (clubName.trim()) {
          const club = await api.createClub(clubName.trim());
          api.setClubId(club.id);
        }
      } else {
        await api.login(email, password);
        // Get user clubs and set first one
        const me = await api.getMe();
        if (me.clubs?.length > 0) {
          api.setClubId(me.clubs[0].club_id);
        }
      }
      onLogin();
    } catch (err: any) {
      setError(err.message || 'Wystąpił błąd');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <form className="login-card" onSubmit={handleSubmit}>
        <h1>WaterPolo Stats</h1>
        <p className="subtitle">
          {isRegister ? 'Utwórz konto i drużynę' : 'Zaloguj się do platformy'}
        </p>

        {error && (
          <div style={{ color: 'var(--red)', fontSize: 13, marginBottom: 16, textAlign: 'center' }}>
            {error}
          </div>
        )}

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
          <div className="form-group">
            <label>Nazwa drużyny</label>
            <input
              type="text"
              value={clubName}
              onChange={e => setClubName(e.target.value)}
              placeholder="KS Waterpolo Kraków"
              required
            />
          </div>
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
