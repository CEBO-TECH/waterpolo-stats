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
