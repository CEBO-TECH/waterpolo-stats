'use client';

import { useState } from 'react';

type MvpRow = {
  player_id: string;
  player_name: string;
  score: number;
  goals: number;
  assists: number;
  steals: number;
  blocks: number;
  turnovers: number;
  fouls: number;
};

type Props = {
  data: { suggested: MvpRow | null; ranking: MvpRow[]; confirmed_player_id: string | null };
  onConfirm: (playerId: string) => void;
  onClose: () => void;
};

const breakdown = (r: MvpRow): string => {
  const parts: string[] = [];
  if (r.goals) parts.push(`${r.goals} g`);
  if (r.assists) parts.push(`${r.assists} as`);
  if (r.steals) parts.push(`${r.steals} prz`);
  if (r.blocks) parts.push(`${r.blocks} blok`);
  if (r.turnovers) parts.push(`${r.turnovers} strat`);
  return parts.join(' · ') || 'brak akcji';
};

export default function MvpSummary({ data, onConfirm, onClose }: Props) {
  const ranking = data.ranking || [];
  const [selected, setSelected] = useState<string>(
    data.confirmed_player_id || data.suggested?.player_id || (ranking[0]?.player_id ?? ''),
  );

  const sel = ranking.find(r => r.player_id === selected) || data.suggested;

  return (
    <div className="popup-overlay" onClick={onClose}>
      <div className="popup popup--wide" onClick={e => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h3 style={{ margin: 0 }}>Podsumowanie meczu — MVP</h3>
          <button className="btn small" onClick={onClose}>✕</button>
        </div>

        {!sel ? (
          <div className="muted">Brak danych do wyłonienia MVP</div>
        ) : (
          <>
            <div className="mvp-hero">
              <div className="mvp-hero__badge">🏅</div>
              <div style={{ flex: 1 }}>
                <div className="muted small">Sugerowany MVP</div>
                <div className="mvp-hero__name">{sel.player_name}</div>
                <div className="muted small">{breakdown(sel)}</div>
              </div>
              <div className="mvp-hero__score">{sel.score}<span className="muted small" style={{ fontSize: 12 }}> pkt</span></div>
            </div>

            <div className="subhead" style={{ marginTop: 16 }}>Ranking — wybierz MVP</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {ranking.map((r, i) => (
                <div
                  key={r.player_id}
                  className={`rank-row${r.player_id === selected ? ' rank-row--sel' : ''}`}
                  style={{ cursor: 'pointer' }}
                  onClick={() => setSelected(r.player_id)}
                >
                  <span className="rank-row__pos">{i + 1}</span>
                  <span style={{ flex: 1 }}>{r.player_name}</span>
                  <span className="muted small">{breakdown(r)}</span>
                  <span style={{ fontWeight: 700, color: 'var(--accent)', minWidth: 42, textAlign: 'right' }}>{r.score}</span>
                </div>
              ))}
            </div>

            <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
              <button className="btn primary" onClick={() => onConfirm(selected)}>Zatwierdź MVP</button>
              <button className="btn" onClick={onClose}>Pomiń</button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
