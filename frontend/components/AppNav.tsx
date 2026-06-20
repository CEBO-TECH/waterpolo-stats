'use client';

import { ClubInfo, Mode } from '@/lib/types';

const ROLE_LABELS: Record<string, string> = {
  owner: 'Właściciel',
  coach: 'Trener',
  player: 'Zawodnik',
};

// ─── Icons (inline SVG, no dependency) ───

const iconProps = {
  width: 20,
  height: 20,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 2,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
};

const Icons: Record<Mode, JSX.Element> = {
  dashboard: (
    <svg {...iconProps}><rect x="3" y="3" width="7" height="9" rx="1" /><rect x="14" y="3" width="7" height="5" rx="1" /><rect x="14" y="12" width="7" height="9" rx="1" /><rect x="3" y="16" width="7" height="5" rx="1" /></svg>
  ),
  score: (
    <svg {...iconProps}><circle cx="12" cy="13" r="8" /><path d="M12 9v4l2 2" /><path d="M9 3h6" /></svg>
  ),
  stats: (
    <svg {...iconProps}><path d="M3 3v18h18" /><rect x="7" y="11" width="3" height="6" /><rect x="12" y="7" width="3" height="10" /><rect x="17" y="13" width="3" height="4" /></svg>
  ),
  players: (
    <svg {...iconProps}><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M22 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /></svg>
  ),
  matches: (
    <svg {...iconProps}><rect x="3" y="4" width="18" height="18" rx="2" /><path d="M16 2v4M8 2v4M3 10h18" /></svg>
  ),
  admin: (
    <svg {...iconProps}><path d="M12 5v14M5 12h14" /></svg>
  ),
  users: (
    <svg {...iconProps}><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" /></svg>
  ),
};

type NavGroup = {
  label: string;
  items: { key: Mode; label: string; adminOnly?: boolean }[];
};

// Single source of truth for navigation. Extend here when adding new screens.
export const NAV_GROUPS: NavGroup[] = [
  {
    label: 'Przegląd',
    items: [
      { key: 'dashboard', label: 'Pulpit' },
      { key: 'stats', label: 'Statystyki' },
    ],
  },
  { label: 'Mecz na żywo', items: [{ key: 'score', label: 'Asystent' }] },
  {
    label: 'Zarządzanie',
    items: [
      { key: 'players', label: 'Zawodnicy' },
      { key: 'matches', label: 'Mecze' },
      { key: 'admin', label: 'Nowy mecz' },
      { key: 'users', label: 'Użytkownicy', adminOnly: true },
    ],
  },
];

type Props = {
  mode: Mode;
  onSelect: (mode: Mode) => void;
  variant: 'sidebar' | 'drawer';
  user: { email: string; role: string } | null;
  onLogout: () => void;
  onClose?: () => void;
  clubs?: ClubInfo[];
  currentClubId?: string;
  onSwitchClub?: (clubId: string) => void;
};

export default function AppNav({
  mode, onSelect, variant, user, onLogout, onClose,
  clubs = [], currentClubId = '', onSwitchClub,
}: Props) {
  const currentClub = clubs.find(c => c.club_id === currentClubId) || clubs[0];
  const roleLabel = currentClub ? (ROLE_LABELS[currentClub.role] || currentClub.role) : '';

  return (
    <nav className={`app-nav app-nav--${variant}`} aria-label="Nawigacja główna">
      <div className="app-nav__brand">
        <span className="app-nav__logo">🤽</span>
        <span className="app-nav__title">Cap Track</span>
        {variant === 'drawer' && (
          <button className="app-nav__close" onClick={onClose} aria-label="Zamknij menu">✕</button>
        )}
      </div>

      {currentClub && (
        <div className="app-nav__club">
          {clubs.length > 1 ? (
            <select
              className="app-nav__club-select"
              value={currentClub.club_id}
              onChange={e => onSwitchClub?.(e.target.value)}
              aria-label="Wybierz klub"
            >
              {clubs.map(c => (
                <option key={c.club_id} value={c.club_id}>{c.club_name}</option>
              ))}
            </select>
          ) : (
            <div className="app-nav__club-name">{currentClub.club_name}</div>
          )}
          {roleLabel && <div className="muted small">{roleLabel}</div>}
        </div>
      )}

      <div className="app-nav__groups">
        {NAV_GROUPS.map(group => {
          const items = group.items.filter(
            it => !it.adminOnly || user?.role === 'owner' || user?.role === 'coach',
          );
          if (items.length === 0) return null;
          return (
          <div className="app-nav__group" key={group.label}>
            <div className="app-nav__group-label">{group.label}</div>
            {items.map(item => (
              <button
                key={item.key}
                className={`nav-item${mode === item.key ? ' active' : ''}`}
                onClick={() => onSelect(item.key)}
                aria-current={mode === item.key ? 'page' : undefined}
              >
                <span className="nav-item__icon">{Icons[item.key]}</span>
                <span className="nav-item__label">{item.label}</span>
              </button>
            ))}
          </div>
          );
        })}
      </div>

      <div className="app-nav__footer">
        {user && <div className="app-nav__user muted">{user.email}</div>}
        <button className="btn small danger" onClick={onLogout}>Wyloguj</button>
        <div className="muted small app-nav__credit">Powered by CEBO.TECH</div>
      </div>
    </nav>
  );
}
