# 05 — Notatki głosowe

> Pomysł: „Notatki głosowe”.

## Cel
Umożliwić trenerowi nagranie krótkiej notatki głosowej (zamiast pisania) podczas meczu — przypiętej do
zdarzenia, meczu lub zawodnika — z opcjonalną transkrypcją na tekst.

## Obecny stan
- Tylko notatka tekstowa: pole `note` w `Event` i input w `ScoreKeeper`.
- W backendzie jest pusty zaczątek `adapters/ai/` — naturalne miejsce na transkrypcję (np. Whisper).
- Brak storage plików.

## Zakres
**In:** nagrywanie audio na froncie (web MediaRecorder + Capacitor na mobile), upload, odtwarzanie,
przypięcie do meczu/zdarzenia, opcjonalna transkrypcja (async).
**Out (faza 2):** automatyczne tagowanie akcji z transkrypcji, wyszukiwanie po treści.

## Model danych / decyzje
- Nowa encja `VoiceNote` (`id`, `club_id`, `match_id`, `player_id?`, `event_id?`, `audio_url`,
  `duration_s`, `transcript?`, `transcript_status` [none|pending|done|failed], `created_by`, `created_at`).
- **Storage:** rekomendacja — S3-kompatybilny (np. MinIO obok Postgresa w Coolify) z presigned upload.
  Wariant minimalny: zapis pliku na wolumenie kontenera + serwowanie przez backend.
- **Transkrypcja:** port `TranscriptionPort` w `domain/ports/external.py`, implementacja w `adapters/ai/`
  (OpenAI/Whisper albo lokalny `faster-whisper`). Uruchamiana async (background task / kolejka) — `transcript_status`.

## Backend (DDD/hexagonal)
- `domain/models/voice_note.py`, port `VoiceNoteRepository` + `TranscriptionPort` + `StoragePort`.
- `domain/services/voice_note_service.py` — tworzenie notatki, zlecenie transkrypcji, aktualizacja statusu.
- `adapters/persistence/repositories/voice_note_repo.py`, `adapters/storage/` (S3/MinIO), `adapters/ai/transcription_*`.
- `api/routes/voice_notes.py`:
  - `POST /v1/clubs/{club_id}/voice-notes` (presigned URL lub multipart) — `CoachOrOwner`.
  - `GET .../matches/{match_id}/voice-notes`, `GET .../voice-notes/{id}` (audio/transkrypt).
  - opcjonalnie `POST .../voice-notes/{id}/transcribe`.
- Migracja tabeli `voice_notes`.

## Frontend / UX (iPad-first)
- Komponent `VoiceRecorder` (przycisk mikrofon w `ScoreKeeper` obok pola notatki): tap-and-hold lub start/stop,
  licznik czasu, podgląd waveform, zapis. Na iPadzie duży przycisk dotykowy.
- Lista notatek głosowych w widoku meczu / przy zdarzeniu: play + (jeśli jest) transkrypt.
- Capacitor: uprawnienia mikrofonu (iOS `NSMicrophoneUsageDescription`, Android `RECORD_AUDIO`).
- Offline: nagranie w kolejce uploadu (reuse wzorca `offline-queue`).

## Kroki implementacji
1. Wybór storage (MinIO/S3 vs wolumen) i transkrypcji (cloud vs lokalna) — decyzja właściciela.
2. Encja + migracja + repo + porty.
3. `voice_note_service` + testy (mock storage/transcription).
4. Routy (upload + listy + transkrypcja) + testy API.
5. `VoiceRecorder` + odtwarzacz + uprawnienia mobile.
6. Async transkrypcja + odświeżanie statusu w UI.

## Kryteria akceptacji
- Trener nagrywa notatkę na iPadzie i odtwarza ją później przy meczu/zdarzeniu.
- (Jeśli włączone) transkrypcja pojawia się po przetworzeniu, z czytelnym statusem.
- Nagranie offline trafia do kolejki i wysyła się po odzyskaniu sieci.

## Zależności
Niezależne od pozostałych. Wymaga decyzji infrastrukturalnych (storage + AI). Można robić równolegle.
