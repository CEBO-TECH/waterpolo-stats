'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

type Props = {
  playerId: string;
  playerLabel: string;
  onClose: () => void;
};

const pct = (v: number) => `${Math.round((v || 0) * 100)}%`;

export default function PlayerProfile({ playerId, playerLabel, onClose }: Props) {
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    (async () => {
      setLoading(true);
      try {
        const data = await api.getPlayerProfile(playerId);
        if (active) setProfile(data);
      } catch {
        if (active) setProfile(null);
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => { active = false; };
  }, [playerId]);

  const kpis = profile ? [
    { label: 'Mecze', value: profile.total_matches },
    { label: 'Gole', value: profile.total_goals },
    { label: 'Skuteczność', value: pct(profile.overall_effectiveness) },
    { label: 'Asysty', value: profile.total_assists },
    { label: 'Straty', value: profile.total_turnovers },
    { label: 'Wykluczenia', value: profile.total_exclusions },
    { label: 'Przejęcia', value: profile.total_steals },
    { label: 'Bloki', value: profile.total_blocks },
  ] : [];

  const trend = profile?.match_trend || [];

  return (
    <div className="popup-overlay" onClick={onClose}>
      <div className="popup popup--wide" onClick={e => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h3 style={{ margin: 0 }}>Profil — {playerLabel}</h3>
          <button className="btn small" onClick={onClose}>✕</button>
        </div>

        {loading ? (
          <div className="muted">Ładowanie...</div>
        ) : !profile ? (
          <div className="muted">Brak danych</div>
        ) : (
          <>
            <div className="kpi-grid">
              {kpis.map(k => (
                <div className="kpi-card" key={k.label}>
                  <div className="kpi-card__value">{k.value}</div>
                  <div className="kpi-card__label">{k.label}</div>
                </div>
              ))}
            </div>

            <div className="subhead" style={{ marginTop: 20 }}>Tendencja per mecz</div>
            {trend.length === 0 ? (
              <div className="muted">Brak rozegranych meczów</div>
            ) : (
              <div className="stats-table-wrap">
                <table className="stats-table">
                  <thead>
                    <tr>
                      <th>Mecz</th>
                      <th>Gole</th>
                      <th>Rzuty</th>
                      <th>Sk.</th>
                      <th>As.</th>
                      <th>Str.</th>
                      <th>Wykl.</th>
                      <th>Prz.</th>
                      <th>Bloki</th>
                    </tr>
                  </thead>
                  <tbody>
                    {trend.map((m: any) => (
                      <tr key={m.match_id}>
                        <td style={{ textAlign: 'left', whiteSpace: 'nowrap' }}>
                          {m.match_date} <span className="muted">vs {m.opponent || '—'}</span>
                        </td>
                        <td>{m.goals || '·'}</td>
                        <td>{m.shots || '·'}</td>
                        <td>{pct(m.shot_effectiveness)}</td>
                        <td>{m.assists || '·'}</td>
                        <td>{m.turnovers || '·'}</td>
                        <td>{m.exclusions || '·'}</td>
                        <td>{m.steals || '·'}</td>
                        <td>{m.blocks || '·'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
