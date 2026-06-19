# 01 — Panel główny (Dashboard statystyk)

> Pomysł: „Statystyki panel główny”.

## Cel
Ekran startowy po zalogowaniu, który w jednym widoku pokazuje stan klubu: aktywny mecz,
najważniejsze statystyki sezonu, ostatnie mecze, top zawodników i szybkie skróty do akcji.

## Obecny stan
- Brak dashboardu. Po zalogowaniu `app/page.tsx` od razu pokazuje tryb `score` (ScoreKeeper).
- Backend ma dane do agregacji: `team_stats_service.compute_season_summary` (W/L/D, rankingi),
  `player_profile_service` (trend), `stats_service` (mecz), `matches`/`seasons` repo.

## Zakres
**In:** nowy tryb `dashboard` jako domyślny po starcie; kafelki KPI; lista ostatnich meczów;
top strzelcy/asystenci; CTA „Wznów aktywny mecz” / „Nowy mecz”.
**Out:** szczegółowe wykresy czasowe (→ `10-statystyki-zaawansowane.md`).

## Backend (DDD/hexagonal)
W większości reuse istniejących serwisów. Dodać jeden zagregowany endpoint, by uniknąć N zapytań z fronta:

- `domain/services/dashboard_service.py` — `DashboardService.compute_overview(matches, season_summary, active_match, recent_n=5)`
  zwraca DTO: `active_match`, `recent_matches[]`, `season_kpis` (mecze, bilans, GF/GA, różnica),
  `top_scorers[]`, `top_assistants[]`.
- Reuse portów: `MatchRepo`, `SeasonRepo`, `EventRepo`. Brak nowych encji i migracji.
- `api/routes/dashboard.py` → `GET /v1/clubs/{club_id}/dashboard?season_id=…&age_category=…` (guard `AnyMember`).
  Rejestracja routera w `src/main.py`.
- Klient: `api.getDashboard(seasonId?, ageCategory?)` w `frontend/lib/api.ts`.

## Frontend / UX (iPad-first)
- Nowy komponent `components/Dashboard.tsx` + tryb `'dashboard'` w `Mode` (`lib/types.ts`),
  ustawiony jako startowy w `app/page.tsx` (zamiast `score`).
- Layout iPad: górny rząd 3–4 kafli KPI; pod nim 2 kolumny — lewa „Ostatnie mecze”, prawa „Top zawodnicy”.
- Karta aktywnego meczu na górze z dużym CTA „Wznów” (przejście do `score`). Telefon: kafle w jednej kolumnie (stack).
- Filtr sezonu/kategorii (selecty) w nagłówku dashboardu.

## Kroki implementacji
1. `DashboardService` + test w `tests/domain/test_dashboard_service.py`.
2. Route `dashboard.py` + rejestracja + test API.
3. `api.getDashboard` + typ DTO w `lib/types.ts`.
4. `Dashboard.tsx`, podpięcie trybu i ustawienie jako domyślny.
5. Skróty nawigacyjne (CTA) do innych trybów.

## Kryteria akceptacji
- Po zalogowaniu widać dashboard z realnymi danymi klubu.
- KPI zgadzają się z `team_stats` dla wybranego sezonu.
- Na iPadzie 2-kolumnowy układ; na telefonie stack; brak poziomego scrolla.

## Zależności
Lekka zależność od `04` (filtr kategorii) i `10` (link do szczegółów). Można wdrożyć z reuse istniejących statystyk.
