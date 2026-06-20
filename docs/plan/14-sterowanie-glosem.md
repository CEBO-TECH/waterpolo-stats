# 14 — Sterowanie głosem (agent komend głosowych)

## Cel
Hands‑free wpisywanie zdarzeń na meczu: trener mówi „numer 12 gol z kontrataku",
a aplikacja od razu rozpoznaje akcję i numer, pokazuje do potwierdzenia i wrzuca
zdarzenie do tej samej kolejki co kliknięcie (z obsługą offline).

## Architektura (hybryda — niezawodność + „wow")
1. **Rozpoznawanie mowy:** Web Speech API w przeglądarce (`lang: pl-PL`).
   Wbudowane w Chrome/Safari, za darmo. Na webie wymaga internetu (audio idzie do
   chmury); prawdziwie offline głos wymagałby natywnej wtyczki iOS (przyszłość).
2. **Parser deterministyczny (rdzeń):** `domain/services/voice_command_service.py`.
   Polskie liczebniki (0–30, formy „dwunastka") + mapa słów kluczowych → jedna z 44
   flag zdarzenia. Działa offline, natychmiast, bez kosztów API, w pełni przewidywalnie.
3. **Warstwa Claude (naturalność + odporność):** `adapters/ai/claude_nlu.py`,
   model Claude **Haiku 4.5**, structured output (JSON). Uruchamiana tylko gdy parser
   nie rozpoznał akcji albo nie znalazł numeru. Klucz API trzyma backend.
4. **Krok potwierdzenia:** chip „#12 — G z kontrataku" z 4‑sekundowym auto‑potwierdzeniem
   (pasek odliczania) + „✓ Zapisz" / „✕ Anuluj". Chroni dane przed przesłyszeniem
   i daje efekt „zrozumiał".

## Backend
- `domain/ports/external.py`: `ParsedCommand`, `VoiceCommandPort`.
- `domain/services/voice_command_service.py`: parser regułowy (diakrytyki foldowane do ASCII).
- `adapters/ai/claude_nlu.py`: `ClaudeVoiceCommandAdapter` + `get_voice_command_port()`
  (zwraca None gdy `VOICE_NLU_BACKEND != "claude"` lub brak `ANTHROPIC_API_KEY`).
- `api/routes/voice.py`: `POST /v1/clubs/{club_id}/voice/parse` → parser → (Claude) →
  rozwiązanie numeru względem składu aktywnego meczu → `VoiceParseResponse`.
- Config: `VOICE_NLU_BACKEND` ("deterministic"|"claude"), `ANTHROPIC_API_KEY`,
  `ANTHROPIC_NLU_MODEL` (domyślnie `claude-haiku-4-5`).
- Dep: `anthropic` (import leniwy — bez klucza nigdy się nie ładuje).

## Frontend
- `lib/api.ts`: `parseVoiceCommand(transcript, matchId)`.
- `components/VoiceCommand.tsx`: przycisk mikrofonu + Web Speech (pl‑PL) + chip
  potwierdzenia z auto‑potwierdzeniem; obsługa braku wsparcia/odmowy mikrofonu.
- `components/ScoreKeeper.tsx`: render `VoiceCommand` w panelu akcji; potwierdzona
  komenda → `createEvents` (ta sama ścieżka offline‑resilient co tap).

## Konfiguracja produkcyjna
- Ustaw `ANTHROPIC_API_KEY` w env backendu (Coolify). Bez klucza działa sam parser
  deterministyczny (`VOICE_NLU_BACKEND=deterministic` lub po prostu brak klucza).

## Status
- [x] Backend: port, parser, adapter Claude, route, config, dep
- [x] Frontend: api, komponent, integracja w ScoreKeeper, style (iPad‑first)
- [x] Testy: 12 jednostkowych parsera + 3 API route (88/88 całego backendu)
- [ ] (Przyszłość) natywna wtyczka iOS do offline‑owego rozpoznawania mowy
- [ ] (Przyszłość) tryb ciągłego nasłuchu (seria komend bez ponownego tapnięcia)
