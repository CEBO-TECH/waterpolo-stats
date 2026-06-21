'use client';

export type BarItem = { label: string; value: number; color?: string };

/** Lightweight CSS bar chart (non-negative values). No external deps. */
export function Bars({
  data,
  color = 'var(--accent)',
  height = 180,
  unit = '',
}: {
  data: BarItem[];
  color?: string;
  height?: number;
  unit?: string;
}) {
  const max = Math.max(1, ...data.map(d => d.value));
  const barArea = height - 34;
  if (data.length === 0) return <div className="muted small">Brak danych</div>;
  return (
    <div className="bars" style={{ height }}>
      {data.map((d, i) => {
        const h = Math.max(2, Math.round((d.value / max) * barArea));
        return (
          <div className="bars__col" key={i}>
            <div className="bars__val">{d.value}{unit}</div>
            <div className="bars__bar" style={{ height: h, background: d.color || color }} />
            <div className="bars__label">{d.label}</div>
          </div>
        );
      })}
    </div>
  );
}

/** Color palette for multi-series overlays (one color per series). */
export const SERIES_PALETTE = [
  'var(--accent)', 'var(--green)', 'var(--orange)', 'var(--yellow)',
  'var(--red)', '#a78bfa', '#f472b6', '#38bdf8', '#fb923c', '#4ade80',
];

/**
 * Overlaid bars: N series grouped per category (non-negative). Used to lay
 * several matches on top of each other for head-to-head comparison.
 */
export function MultiSeriesBars({
  categories,
  series,
  height = 200,
}: {
  categories: string[];
  series: { name: string; color: string; values: number[] }[];
  height?: number;
}) {
  const max = Math.max(1, ...series.flatMap(s => s.values));
  const barArea = height - 34;
  const barW = Math.max(6, Math.min(18, Math.round(96 / Math.max(1, series.length))));
  if (series.length === 0 || categories.length === 0)
    return <div className="muted small">Brak danych</div>;
  return (
    <>
      <div className="bars" style={{ height }}>
        {categories.map((c, i) => (
          <div className="bars__col" key={c}>
            <div style={{ display: 'flex', gap: 3, alignItems: 'flex-end' }}>
              {series.map((s, si) => (
                <div
                  key={si}
                  className="bars__bar"
                  title={`${s.name}: ${s.values[i] ?? 0}`}
                  style={{
                    height: Math.max(2, Math.round(((s.values[i] || 0) / max) * barArea)),
                    background: s.color,
                    width: barW,
                  }}
                />
              ))}
            </div>
            <div className="bars__label">{c}</div>
          </div>
        ))}
      </div>
      <div className="chart-legend">
        {series.map((s, si) => (
          <span className="muted small" key={si}>
            <span style={{ color: s.color }}>■</span> {s.name}
          </span>
        ))}
      </div>
    </>
  );
}

/** Grouped bars: two series side-by-side per category (non-negative). */
export function GroupedBars({
  categories,
  seriesA,
  seriesB,
  height = 180,
}: {
  categories: string[];
  seriesA: { name: string; color: string; values: number[] };
  seriesB: { name: string; color: string; values: number[] };
  height?: number;
}) {
  const max = Math.max(1, ...seriesA.values, ...seriesB.values);
  const barArea = height - 34;
  const bar = (v: number, color: string) => (
    <div className="bars__bar" style={{ height: Math.max(2, Math.round((v / max) * barArea)), background: color, width: 14 }} />
  );
  return (
    <>
      <div className="bars" style={{ height }}>
        {categories.map((c, i) => (
          <div className="bars__col" key={c}>
            <div style={{ display: 'flex', gap: 4, alignItems: 'flex-end' }}>
              {bar(seriesA.values[i] || 0, seriesA.color)}
              {bar(seriesB.values[i] || 0, seriesB.color)}
            </div>
            <div className="bars__label">{c}</div>
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', gap: 16, justifyContent: 'center', marginTop: 4 }}>
        <span className="muted small"><span style={{ color: seriesA.color }}>■</span> {seriesA.name}</span>
        <span className="muted small"><span style={{ color: seriesB.color }}>■</span> {seriesB.name}</span>
      </div>
    </>
  );
}
