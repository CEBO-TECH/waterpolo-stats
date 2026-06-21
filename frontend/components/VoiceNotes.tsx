'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { api } from '@/lib/api';

type Props = {
  matchId: string;
  showToast: (m: string) => void;
  canRecord: boolean;
  playerId?: string | null;
};

const fmt = (s: number) => {
  const m = Math.floor(s / 60);
  return `${m}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
};

export default function VoiceNotes({ matchId, showToast, canRecord, playerId }: Props) {
  const [notes, setNotes] = useState<any[]>([]);
  const [recording, setRecording] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const recRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const startRef = useRef<number>(0);
  const tickRef = useRef<any>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const load = useCallback(async () => {
    if (!matchId) return;
    setNotes(await api.getVoiceNotes(matchId));
  }, [matchId]);

  useEffect(() => { load(); }, [load]);

  const startRecording = async () => {
    if (!navigator.mediaDevices?.getUserMedia) return showToast('Brak dostępu do mikrofonu');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      // Pick a format the browser can actually record AND replay. Safari records
      // mp4 (not webm), so forcing 'audio/webm' produced unplayable notes there.
      const mime = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4'].find(
        m => (window as any).MediaRecorder?.isTypeSupported?.(m),
      );
      const rec = mime ? new MediaRecorder(stream, { mimeType: mime }) : new MediaRecorder(stream);
      chunksRef.current = [];
      rec.ondataavailable = e => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      rec.onstop = async () => {
        stream.getTracks().forEach(t => t.stop());
        clearInterval(tickRef.current);
        const blob = new Blob(chunksRef.current, { type: rec.mimeType || mime || 'audio/webm' });
        const duration = Math.round((Date.now() - startRef.current) / 1000);
        setRecording(false);
        try {
          await api.uploadVoiceNote(matchId, blob, { duration_s: duration, player_id: playerId || undefined });
          showToast('Zapisano notatkę');
          load();
        } catch (e: any) {
          showToast(e.message || 'Błąd zapisu');
        }
      };
      recRef.current = rec;
      startRef.current = Date.now();
      setElapsed(0);
      tickRef.current = setInterval(() => setElapsed(Math.round((Date.now() - startRef.current) / 1000)), 250);
      rec.start();
      setRecording(true);
    } catch {
      showToast('Nie udało się uruchomić mikrofonu');
    }
  };

  const stopRecording = () => recRef.current?.stop();

  const play = async (noteId: string) => {
    try {
      const url = await api.getVoiceNoteAudioUrl(matchId, noteId);
      if (!url) return showToast('Brak nagrania');
      // Retain the element (a local `new Audio(...)` can be GC'd mid-playback on
      // the web) and surface decode/playback failures instead of failing silently.
      audioRef.current?.pause();
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onerror = () => showToast('Nie można odtworzyć nagrania w tej przeglądarce');
      await audio.play();
    } catch {
      showToast('Nie można odtworzyć nagrania');
    }
  };

  const del = async (noteId: string) => {
    if (!confirm('Usunąć notatkę głosową?')) return;
    try { await api.deleteVoiceNote(matchId, noteId); load(); }
    catch (e: any) { showToast(e.message || 'Błąd'); }
  };

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <div className="subhead" style={{ margin: 0 }}>Notatki głosowe</div>
        {canRecord && (
          recording ? (
            <button className="btn small danger" onClick={stopRecording}>
              ⏹ Zatrzymaj ({fmt(elapsed)})
            </button>
          ) : (
            <button className="btn small primary" onClick={startRecording}>🎙 Nagraj</button>
          )
        )}
      </div>
      <div className="events-list">
        {notes.length === 0 ? (
          <div className="muted">Brak notatek</div>
        ) : (
          notes.map(n => (
            <div key={n.id} className="event-item">
              <button className="btn small" onClick={() => play(n.id)}>▶</button>
              <span className="event-action">{n.note || 'Notatka'}</span>
              <span className="muted small">{n.duration_s ? fmt(n.duration_s) : ''}</span>
              <span className="event-player">{n.created_by?.split('@')[0]}</span>
              {canRecord && <button className="btn small danger" onClick={() => del(n.id)}>✕</button>}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
