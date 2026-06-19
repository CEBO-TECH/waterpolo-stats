# 13 — Zmiany (woda/ławka) i czas gry zawodników

> Pomysł: „Łatwiejsze prowadzenie statystyk — wprowadzić zmiany, żeby wiadomo było kto ile zagrał i ile w tym czasie
> zrobił. Podzielić strzałkami woda/ławka: wchodzi → strzałka, schodzi → strzałka; dzięki temu wiemy ile czasu zawodnicy grają”.

## Cel
Rejestrować wejścia/zejścia zawodników (zmiany), liczyć czas spędzony w wodzie, i wiązać statystyki
z czasem gry (np. gole/straty na minutę, kto był w wodzie podczas akcji).

## Obecny stan
- Brak modelu zmian i czasu gry. `ScoreKeeper` zna tylko skład meczu i wybranego zawodnika.
- Brak zegara meczowego (potrzebny też dla `10` — rozkład czasowy).
- Events mają `timestamp` (zegar ścienny), `quarter`, `video_timestamp` (gdy stream).

## Decyzje projektowe
- **Zegar gry.** Wprowadzić lekki stan czasu meczu: start/stop kwarty (timer) → `game_clock_s`.
  Minimalnie: liczyć czas od startu kwarty (front trzyma timer, backend zapisuje znaczniki).
  Spójne z osią czasu z `06` (gdy jest stream — można użyć `video_timestamp`).
- **Model zmian.** Encja `Substitution` / `StintEvent`:
  `id`, `club_id`, `match_id`, `player_id`, `direction` [in|out], `quarter`, `game_clock_s?`, `video_timestamp?`, `timestamp`.
  Czas gry = suma odcinków (in→out). Otwarty odcinek na koniec kwarty/meczu domykany automatycznie.
- **Stan „w wodzie”.** Wyliczany ze zmian; przy każdym evencie można zapisać, kto był w wodzie (opcjonalnie:
  pole/relacja `event_on_water`), albo wyliczać post-hoc z odcinków.

## Backend (DDD/hexagonal)
- `domain/models/substitution.py` (encja zmiany) + ewentualnie `lineup` (stan wody).
- `domain/services/playtime_service.py`:
  - `apply_substitution(...)`, `compute_time_on_water(subs, match_len) -> {player_id: seconds}`,
  - domykanie otwartych odcinków, walidacje (nie wejście gdy już w wodzie, max 6+GK w polu — ostrzeżenia).
- Port `SubstitutionRepository` + adapter + migracja `substitutions`.
- Routy:
  - `POST /v1/clubs/{club_id}/matches/{match_id}/substitutions` (in/out) — `CoachOrOwner`.
  - `GET .../matches/{match_id}/playtime` → czas gry per zawodnik + odcinki.
  - integracja w `stats`: statystyki na minutę / w przeliczeniu na czas gry.

## Frontend / UX (iPad-first)
- W `ScoreKeeper`: panel składu podzielony na **WODA** / **ŁAWKA**.
  - Strzałka ▲ przy zawodniku na ławce = wchodzi (→ woda); strzałka ▼ przy zawodniku w wodzie = schodzi (→ ławka).
  - Jeden tap = zmiana; wizualnie przenosi kartę między sekcjami; licznik „w wodzie: mm:ss” na żywo.
  - Timer kwarty (start/stop) sterujący `game_clock`.
- Akcje statystyczne rejestrowane domyślnie dla zawodników „w wodzie” (szybszy wybór).
- Widok „Czas gry” w statystykach meczu: pasek/oś z odcinkami gry każdego zawodnika (Gantt-like).
- iPad-first: dwie kolumny WODA/ŁAWKA + duże strzałki dotykowe; telefon: sekcje jedna pod drugą.

## Kroki implementacji
1. Timer kwarty + `game_clock_s` (front) + zapis znaczników (start/stop kwarty).
2. Encja `Substitution` + repo + migracja.
3. `playtime_service` (czas w wodzie, domykanie odcinków) + testy.
4. Routy substitutions + playtime + integracja w stats (per minuta).
5. UI WODA/ŁAWKA + strzałki + licznik czasu w `ScoreKeeper`.
6. Widok „Czas gry” (oś/Gantt) w statystykach.

## Kryteria akceptacji
- Wejścia/zejścia rejestruje się jednym tapem; karta przenosi się WODA↔ŁAWKA.
- Czas gry per zawodnik liczy się poprawnie (odcinki sumowane, otwarte domknięte).
- Statystyki można pokazać w przeliczeniu na czas gry; widać oś czasu gry zawodników.

## Zależności
Dostarcza zegar meczowy i czas gry dla `10` (rozkład czasowy, per-minuta) i `11` (normalizacja MVP).
Najlepiej po ustabilizowaniu `ScoreKeeper` i przed/wraz z `10`.
