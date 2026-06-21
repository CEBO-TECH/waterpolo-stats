'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { Capacitor } from '@capacitor/core';
import { api } from '@/lib/api';
import type { ParsedVoiceCommand } from '@/lib/types';

// Minimal typing for the Web Speech API (not in lib.dom for all targets).
type SpeechRecognitionLike = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onresult: ((e: any) => void) | null;
  onerror: ((e: any) => void) | null;
  onend: (() => void) | null;
};

function getRecognitionCtor(): (new () => SpeechRecognitionLike) | null {
  if (typeof window === 'undefined') return null;
  return (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition || null;
}

const AUTO_CONFIRM_MS = 4000;

type Status = 'idle' | 'listening' | 'parsing' | 'confirm' | 'error';

type Props = {
  matchId: string;
  disabled?: boolean;
  onConfirm: (cmd: ParsedVoiceCommand) => void;
  showToast: (msg: string) => void;
};

export default function VoiceCommand({ matchId, disabled, onConfirm, showToast }: Props) {
  const [supported, setSupported] = useState(true);
  const [status, setStatus] = useState<Status>('idle');
  const [pending, setPending] = useState<ParsedVoiceCommand | null>(null);
  const [remaining, setRemaining] = useState(AUTO_CONFIRM_MS);

  const recRef = useRef<SpeechRecognitionLike | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Native app uses the iOS/Android speech plugin; web uses the Web Speech API.
  useEffect(() => { setSupported(Capacitor.isNativePlatform() || !!getRecognitionCtor()); }, []);

  const clearTimer = () => {
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
  };

  const dismiss = useCallback(() => {
    clearTimer();
    setPending(null);
    setStatus('idle');
  }, []);

  const confirm = useCallback((cmd: ParsedVoiceCommand) => {
    clearTimer();
    onConfirm(cmd);
    setPending(null);
    setStatus('idle');
  }, [onConfirm]);

  const startCountdown = useCallback((cmd: ParsedVoiceCommand) => {
    clearTimer();
    const end = Date.now() + AUTO_CONFIRM_MS;
    setRemaining(AUTO_CONFIRM_MS);
    timerRef.current = setInterval(() => {
      const left = end - Date.now();
      if (left <= 0) { confirm(cmd); } else { setRemaining(left); }
    }, 100);
  }, [confirm]);

  const handleTranscript = useCallback(async (transcript: string) => {
    setStatus('parsing');
    try {
      const cmd = await api.parseVoiceCommand(transcript, matchId);
      setPending(cmd);
      if (cmd.matched) {
        setStatus('confirm');
        startCountdown(cmd);
      } else {
        setStatus('error');
      }
    } catch {
      setPending({ matched: false, transcript, reason: 'Brak połączenia z serwerem' });
      setStatus('error');
    }
  }, [matchId, startCountdown]);

  // Native (iOS/Android) — Apple Speech / Android SpeechRecognizer via the plugin.
  // Works in the WKWebView where Web Speech is unavailable, and can run on-device offline.
  const listenNative = useCallback(async () => {
    try {
      const { SpeechRecognition } = await import('@capgo/capacitor-speech-recognition');
      const perm = await SpeechRecognition.requestPermissions();
      if (perm.speechRecognition !== 'granted') return showToast('Brak zgody na mikrofon / rozpoznawanie mowy');
      clearTimer();
      setPending(null);
      setStatus('listening');
      const res = await SpeechRecognition.start({
        language: 'pl-PL', maxResults: 1, partialResults: false, popup: false,
      });
      const transcript = (res?.matches?.[0] || '').trim();
      if (transcript) await handleTranscript(transcript);
      else setStatus('idle');
    } catch {
      setStatus('idle');
      showToast('Błąd rozpoznawania mowy');
    }
  }, [handleTranscript, showToast]);

  const listen = useCallback(() => {
    if (disabled) return showToast('Mecz zakończony');
    if (Capacitor.isNativePlatform()) return void listenNative();
    const Ctor = getRecognitionCtor();
    if (!Ctor) { setSupported(false); return; }
    clearTimer();
    setPending(null);
    const rec = new Ctor();
    rec.lang = 'pl-PL';
    rec.continuous = false;
    rec.interimResults = false;
    rec.onresult = (e: any) => {
      const transcript = e.results?.[0]?.[0]?.transcript ?? '';
      if (transcript.trim()) handleTranscript(transcript.trim());
      else setStatus('idle');
    };
    rec.onerror = (e: any) => {
      setStatus('idle');
      if (e?.error === 'not-allowed') showToast('Brak dostępu do mikrofonu');
      else if (e?.error !== 'no-speech' && e?.error !== 'aborted') showToast('Błąd rozpoznawania mowy');
    };
    rec.onend = () => { setStatus(s => (s === 'listening' ? 'idle' : s)); };
    recRef.current = rec;
    try { rec.start(); setStatus('listening'); } catch { setStatus('idle'); }
  }, [disabled, listenNative, handleTranscript, showToast]);

  const stopListening = useCallback(() => {
    if (Capacitor.isNativePlatform()) {
      import('@capgo/capacitor-speech-recognition').then(
        ({ SpeechRecognition }) => SpeechRecognition.stop().catch(() => {}),
      );
    } else {
      recRef.current?.stop();
    }
    setStatus('idle');
  }, []);

  useEffect(() => () => { clearTimer(); recRef.current?.abort(); }, []);

  if (!supported) {
    return (
      <div className="voice-cmd voice-cmd--unsupported muted small" title="Przeglądarka nie wspiera rozpoznawania mowy">
        🎤 Sterowanie głosem niedostępne w tej przeglądarce
      </div>
    );
  }

  const listening = status === 'listening';
  const parsing = status === 'parsing';
  const pct = Math.max(0, Math.min(100, (remaining / AUTO_CONFIRM_MS) * 100));

  return (
    <div className="voice-cmd">
      <button
        className={`voice-cmd__mic${listening ? ' listening' : ''}`}
        onClick={listening ? stopListening : listen}
        disabled={disabled || parsing}
        aria-label={listening ? 'Słucham…' : 'Komenda głosowa'}
        title='Powiedz np. „numer 12 gol z kontrataku”'
      >
        <span className="voice-cmd__icon">🎤</span>
        <span className="voice-cmd__text">
          {listening ? 'Słucham…' : parsing ? 'Rozpoznaję…' : 'Komenda głosem'}
        </span>
      </button>

      {pending && status === 'confirm' && pending.matched && (
        <div className="voice-confirm" role="status">
          <div className="voice-confirm__main">
            <span className="voice-confirm__num">#{pending.number}</span>
            <span className="voice-confirm__label">{pending.label}</span>
            {pending.source === 'claude' && <span className="voice-confirm__badge" title="Rozpoznane przez Claude">AI</span>}
          </div>
          <div className="voice-confirm__sub muted small">„{pending.transcript}”</div>
          <div className="voice-confirm__actions">
            <button className="btn small primary" onClick={() => confirm(pending)}>✓ Zapisz</button>
            <button className="btn small" onClick={dismiss}>✕ Anuluj</button>
          </div>
          <div className="voice-confirm__bar"><span style={{ width: `${pct}%` }} /></div>
        </div>
      )}

      {pending && status === 'error' && !pending.matched && (
        <div className="voice-confirm voice-confirm--error" role="status">
          <div className="voice-confirm__main">
            <span className="voice-confirm__warn">⚠︎</span>
            <span className="voice-confirm__label">{pending.reason || 'Nie rozpoznano'}</span>
          </div>
          {pending.transcript && <div className="voice-confirm__sub muted small">„{pending.transcript}”</div>}
          <div className="voice-confirm__actions">
            <button className="btn small" onClick={listen}>🎤 Powtórz</button>
            <button className="btn small" onClick={dismiss}>✕</button>
          </div>
        </div>
      )}
    </div>
  );
}
