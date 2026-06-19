'use client';

type Props = {
  videoId: string;
  seekSeconds: number;
  title?: string;
  onClose: () => void;
};

export default function VideoModal({ videoId, seekSeconds, title, onClose }: Props) {
  const src = `https://www.youtube.com/embed/${videoId}?start=${Math.max(0, seekSeconds)}&autoplay=1`;
  return (
    <div className="popup-overlay" onClick={onClose}>
      <div className="popup popup--wide" onClick={e => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h3 style={{ margin: 0 }}>{title || 'Powtórka akcji'}</h3>
          <button className="btn small" onClick={onClose}>✕</button>
        </div>
        <div className="video-embed">
          <iframe
            src={src}
            title="YouTube"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
            allowFullScreen
          />
        </div>
      </div>
    </div>
  );
}
