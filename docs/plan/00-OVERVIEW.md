# Plan rozwoju WTS Stats — przegląd

Ten katalog zawiera plany implementacji kolejnych funkcji aplikacji do statystyk piłki wodnej.
Każdy plik = jedna spójna funkcja (epik) z planem wdrożenia. Implementujemy **kolejno**, wg roadmapy poniżej.

## Zasady przekrojowe (obowiązują we wszystkich planach)

- **UX iPad-first.** Każdy widok projektujemy najpierw pod iPada (tablet landscape ~1024–1366 px),
  dopiero potem zwężamy do telefonu. Duże dotykowe cele (≥44 px), layout 2-kolumnowy na tablecie,
  ciemny motyw. Używamy istniejących design-tokenów z `frontend/app/globals.css`
  (`--accent`, `--bg-card`, `--border`, `--radius`, …). Dotyczy weba i aplikacji mobilnej (Capacitor).
- **Backend: uproszczony DDD + hexagonal.** Warstwy:
  `domain/models` (dataclasses) → `domain/ports` (interfejsy) → `domain/services` (logika)
  → `adapters/` (persistence/auth/ai/youtube) → `api/routes` (cienkie kontrolery) + `api/deps.py` (DI, guardy ról).
  Role: `OwnerOnly`, `CoachOrOwner`, `AnyMember`.
- **Testy.** Każdy nowy serwis domenowy ma testy w `backend/tests/domain/`, kluczowe przepływy w `backend/tests/api/`.
- **Migracje.** Zmiany schematu przez Alembic (`backend/alembic/versions/`).

## Stan obecny (co już jest)

**Backend** (`backend/`, FastAPI, hexagonal):
- Encje: `Club`, `Season`, `Player` (+`PlayerAgeCategory`), `Match` (`age_category`, `season_id`, wyniki kwart),
  `Event` (44 flagi + `video_timestamp`), `User` + `ClubMembership` (OWNER/COACH/PLAYER),
  `RosterEntry`, `ClubSettings`, `YouTubeStream`, `ClubConfig`.
- Serwisy: `auth`, `config`, `event`, `stats`, `team_stats` (sezon, W/L/D, rankingi), `player_profile` (trend per mecz), `youtube`.
- Routy: `auth`, `bootstrap`, `clubs` (+`/invite`), `config`, `events`, `matches`, `players`, `seasons`, `settings`, `stats`, `youtube`.
- Puste adaptery-zaczątki: `adapters/ai/`, `adapters/youtube/`.

**Frontend** (`frontend/`, Next.js + Capacitor):
- `app/page.tsx` — shell: header (wybór meczu, kwarty, przyciski trybów inline), drawer (burger **ukryty** `display:none`), popupy.
- Komponenty: `LoginPage`, `ScoreKeeper`, `StatsPanel` (tylko tabela), `PlayersPanel` (numer+imię), `MatchesPanel`, `AdminPanel`.
- `lib/api.ts` — pełny klient (auth, clubs, players, matches, events, stats, youtube, config), kolejka offline.

## Mapa pomysłów → pliki

| # pomysłu (z listy) | Plik planu | Stan startowy |
|---|---|---|
| Statystyki panel główny | `01-dashboard.md` | NOWE |
| Burger menu | `02-burger-menu-nawigacja.md` | jest drawer, burger ukryty |
| Logowanie per klub | `03-logowanie-i-kluby.md` | działa, brak przełącznika klubów |
| Globalni zawodnicy w grupach + mecz per grupa + mecz bez grupy + auto-skład | `04-grupy-wiekowe.md` | model jest, brak UI / filtrowania |
| Notatki głosowe | `05-notatki-glosowe.md` | NOWE (jest tylko notatka tekstowa) |
| Link do streamu + znaczniki wideo | `06-stream-i-wideo.md` | backend jest, brak UI / capture timestamp |
| Wiele kont per klub + panel userów | `07-konta-klubu-i-zarzadzanie-userami.md` | jest `/invite`, brak listy/UI |
| Panel zarządzania zawodnikami | `08-panel-zawodnikow.md` | jest podstawowy |
| Panel zarządzania meczami + mecz bez składu | `09-panel-meczow.md` | jest podstawowy |
| Zaawansowane statystyki: wykresy, multi-mecz, rozkład czasowy, indeks of./def. | `10-statystyki-zaawansowane.md` | częściowo (backend trend), brak wykresów |
| Sugerowanie MVP po meczu | `11-mvp-po-meczu.md` | NOWE |
| Konta zawodników + rocznik + logowanie zawodnika | `12-konta-zawodnikow.md` | NOWE (Player ≠ User) |
| Zmiany i czas gry (woda/ławka, strzałki) | `13-zmiany-i-czas-gry.md` | NOWE |
| Sterowanie głosem (agent komend) | `14-sterowanie-glosem.md` | NOWE (Web Speech + parser + Claude Haiku) |

## Proponowana kolejność implementacji (z zależnościami)

Kolejność dobrana tak, by najpierw uporządkować nawigację i fundamenty danych, a dopiero potem
budować na nich analizę i funkcje zaawansowane. Można modyfikować.

1. **`02` Burger menu + nawigacja** — szybki UX-owy fundament dla wszystkich nowych ekranów.
2. **`03` Logowanie i przełącznik klubów** — poprawne wejście do aplikacji.
3. **`08` Panel zawodników** (rozbudowa) — baza pod kategorie wiekowe.
4. **`04` Grupy wiekowe** — fundament danych dla filtrowania składów i statystyk (zależy od `08`).
5. **`09` Panel meczów + mecz bez składu** — porządkuje cykl życia meczu (zależy od `04`).
6. **`01` Dashboard** — agreguje dane z powyższych.
7. **`06` Stream + znaczniki wideo** — wzbogaca rejestrację akcji.
8. **`13` Zmiany i czas gry** — nowa warstwa zbierania danych w `ScoreKeeper`.
9. **`10` Statystyki zaawansowane** — wykresy, multi-mecz, rozkład czasowy (korzysta z `13` i `06`).
10. **`11` MVP po meczu** — pochodna statystyk (zależy od `10`).
11. **`07` Wiele kont per klub + panel userów** — administracja zespołu.
12. **`12` Konta zawodników + rocznik** — rozszerza `07`/`08` o samoobsługę zawodników.
13. **`05` Notatki głosowe** — niezależne, wymaga adaptera AI/storage; można wpleść równolegle.

## Status (uzupełniać w trakcie)

- [x] 02 Burger menu — sidebar (iPad/desktop) + burger/drawer (telefon), `components/AppNav.tsx`
- [x] 03 Logowanie i kluby — `POST /v1/auth/select-club`, wybór klubu po loginie (0/1/wiele), przełącznik w nawigacji
- [x] 08 Panel zawodników — `PUT /players/{id}`, kategorie w liście/bootstrapie, szukajka/sort/filtr, edycja z chipami kategorii, profil zawodnika (`PlayerProfile`).
- [x] 04 Grupy wiekowe — encja `AgeCategory` (słownik per klub) + migracja + seed + CRUD; kategorie w bootstrapie; zarządzanie słownikiem w PlayersPanel; AdminPanel: wybór grupy → auto-podpowiedź składu + filtr (search override); „Bez kategorii”; fix camelCase→snake_case `age_category` przy zapisie meczu.
- [x] 09 Panel meczów — `PUT .../matches/{id}/roster` (skład później/edycja), `roster_count` w liście+bootstrapie, `RosterEditor` (DRY: AdminPanel+MatchesPanel), „Utwórz bez składu”, ustaw aktywny z listy, filtry status/kategoria, badge aktywnego meczu.
- [x] 01 Dashboard — `DashboardService` + `GET /dashboard` (KPI sezonu, W/L/D, GF/GA, top strzelcy/asystenci, ostatnie mecze, aktywny mecz); `Dashboard.tsx` jako domyślny ekran; CTA „Wznów mecz”/„Nowy mecz”; filtr kategorii. `EventRepository.get_all_for_club`.
- [x] 06 Stream + wideo — `start_now` (serwerowy zegar) + `video_id`/`seek_seconds` w `/events/{id}/video-url`; `AppState.youtube`; popup „Stream” w MatchesPanel (link + „Ustaw start = teraz”); ScoreKeeper: pasek statusu streamu + ▶ przy akcjach → `VideoModal` (osadzony YouTube od sekundy z cofnięciem 30s).
- [x] 13 Zmiany i czas gry — encja `Substitution` + migracja; `PlaytimeService` (sumowanie odcinków in→out, otwarte domykane); routy `POST/GET substitutions`, `GET playtime`; auto-domknięcie przy `end_match`; ScoreKeeper: podział WODA/ŁAWKA ze strzałkami ▲/▼ + live licznik czasu gry per zawodnik.
- [x] 10 Statystyki zaawansowane — `AnalyticsService` (multi-mecz agregacja + rozkład per kwarta + indeks of/def) + `POST /stats/multi`; StatsPanel z zakładkami Tabela/Wykresy/Porównaj; lekkie wykresy CSS (`Bars`/`GroupedBars`, bez zależności); KPI + tabela of/def per mecz. (Within-quarter game-clock distribution + konfigurowalne wagi — odłożone.)
- [x] 11 MVP — `MvpService` (ważony scoring wkładu) + `GET/PUT .../matches/{id}/mvp` + kolumna `Match.mvp_player_id` + migracja; po `endMatch` ekran „Podsumowanie meczu” (`MvpSummary`) z sugerowanym MVP, rankingiem i zatwierdzaniem/zmianą.
- [x] 07 Konta klubu + userzy — członkowie (`GET/PATCH/DELETE members` + guard ostatniego ownera), rozszerzony `/invite` (istniejący→od razu, nowy→`ClubInvitation` z tokenem), `GET/DELETE invitations`, `POST /v1/invitations/{token}/accept`; `UsersPanel` (lista/role/usuwanie/zaproszenia+link), nav „Użytkownicy” (owner/coach), obsługa `?invite=` po loginie. Migracja `club_invitations`.
- [x] 12 Konta zawodników — `Player.birth_year/email/user_id` + migracja; powiązanie konta przez przyjęcie zaproszenia (auto-link po emailu); `GET /me/player` + `GET /me/matches`; PlayersPanel: rocznik/email + „Zaproś”/„✓ konto”; `PlayerView` — zawodnik (rola PLAYER) widzi tylko swoje statystyki i mecze (bez paneli zarządzania).
- [x] 05 Notatki głosowe — encja `VoiceNote` + migracja; `StoragePort` z `LocalStorageAdapter` (dev/test) i `S3StorageAdapter` (MinIO/S3, prod, boto3 lazy); `POST/GET/DELETE voice-notes` + `GET .../audio` (proxy z auth); MinIO w `docker-compose.prod.yaml`; `VoiceNotes` w ScoreKeeper (nagrywanie MediaRecorder + lista + odtwarzanie). Bez transkrypcji (świadoma decyzja).
- [x] 14 Sterowanie głosem — agent komend: `VoiceCommandPort`/`ParsedCommand`, parser deterministyczny (`VoiceCommandService`, liczebniki PL + mapa słów→flaga), warstwa Claude Haiku 4.5 (`ClaudeVoiceCommandAdapter`, structured output, leniwy import), `POST /voice/parse` (parser→Claude→rozwiązanie numeru wg składu); frontend: `parseVoiceCommand`, `VoiceCommand.tsx` (Web Speech pl‑PL + chip potwierdzenia z auto‑zapisem), integracja w ScoreKeeper → `createEvents` (offline‑resilient). Config `VOICE_NLU_BACKEND`/`ANTHROPIC_API_KEY`/`ANTHROPIC_NLU_MODEL`. 12 testów parsera + 3 API.
