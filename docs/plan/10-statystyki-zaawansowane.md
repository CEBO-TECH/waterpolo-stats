# 10 — Statystyki zaawansowane: wykresy, multi-mecz, rozkład czasowy, indeks of./def.

> Pomysł: „Panel statystyk z meczu + wykresy dynamiczne; zaznaczyć kilka meczów → sumowanie i tendencja per mecz;
> zbierać timestampy kliknięć i pokazywać rozkład wydarzeń w czasie (kwarty i w obrębie kwart);
> określić co na plus/minus do ataku i obrony, zsumować i wyznaczyć ofensywność/defensywność w funkcji czasu meczu”.

## Cel
Rozbudować analitykę z surowej tabeli do interaktywnych wykresów: pojedynczy mecz, porównanie/sumowanie wielu meczów,
rozkład czasowy zdarzeń oraz wskaźniki ofensywności/defensywności w czasie.

## Obecny stan
- `StatsPanel` to tabela (flagi × zawodnicy, filtr kwarty). Brak wykresów.
- Backend: `stats_service` (mecz), `player_profile_service` (trend per mecz), `team_stats_service` (sezon).
- Każdy `Event` ma `timestamp` (zegar ścienny), `quarter`, oraz `video_timestamp` (sek. od startu streamu, gdy jest stream).
- **Brak** zegara meczowego (game clock) — to kluczowe dla rozkładu „w obrębie kwarty”.

## Decyzje projektowe
1. **Oś czasu meczu.** Do rozkładu czasowego potrzebny wspólny czas gry. Opcje:
   - (A) `video_timestamp` (gdy stream podpięty — `06`) — najprostsze, realne.
   - (B) zegar meczowy liczony od startu kwarty (wymaga `13`/timera kwart).
   - (C) fallback: względny czas od pierwszego eventu w kwarcie.
   Rekomendacja: wspierać (A) gdy dostępne, inaczej (C); docelowo (B) po `13`.
2. **Wagi of./def.** Słownik mapujący każdą z 44 flag na wkład ofensywny/defensywny (+/−),
   konfigurowalny per klub (rozszerzenie `ClubConfig.button_layout`/nowe pole `stat_weights`).
   Indeks ofensywności = ważona suma flag ofensywnych; defensywności analogicznie.

## Backend (DDD/hexagonal)
- `domain/services/analytics_service.py`:
  - `aggregate_multi_match(matches, events)` — suma flag i trend per mecz dla wybranych meczów.
  - `time_distribution(events, bins)` — histogram zdarzeń po koszach czasu (kwarta / minuty / video_timestamp).
  - `offense_defense_index(events, weights, by_time)` — krzywa ofensywności/defensywności w czasie.
- Wagi: `domain/models/stat_weights.py` + domyślny słownik; walidacja w serwisie.
- Routy (`api/routes/stats.py` rozbudowa lub nowy `analytics.py`):
  - `POST /v1/clubs/{club_id}/stats/multi` (body: `match_ids[]`, filtry) → agregaty + trend.
  - `GET .../matches/{match_id}/time-distribution` → histogram.
  - `GET .../matches/{match_id}/oddi` (offense/defense index) lub w multi.
  - `GET/PUT .../config/stat-weights`.
- Reuse `EventRepo.get_all_for_*`. Migracja tylko jeśli wagi w osobnej tabeli (można w `ClubConfig`).

## Frontend / UX (iPad-first)
- Biblioteka wykresów: rekomendacja **Recharts** (lekka, responsywna) — dodać do `frontend/package.json`.
- `StatsPanel` → zakładki: **Mecz** (tabela + wykresy), **Porównaj mecze** (multiselect meczów), **Rozkład czasowy**, **Of./Def.**.
  - Mecz: bar/stacked per zawodnik (gole, straty, skuteczność), donut udziału.
  - Porównaj: wybór wielu meczów (checkboxy) → linia trendu per mecz + tabela zsumowana.
  - Rozkład czasowy: histogram zdarzeń po kwartach i w obrębie kwarty; filtr typ akcji / zawodnik / drużyna.
  - Of./Def.: krzywa indeksu w czasie meczu (area chart), z możliwością nałożenia kilku meczów.
- Edytor wag of./def. (ustawienia): lista flag z suwakami/wartościami +/−.
- iPad: wykresy duże, 2 na rząd; legendy klikalne; tooltipy dotykowe. Telefon: 1 wykres/rząd, scroll pionowy.

## Kroki implementacji
1. `analytics_service` + testy (multi-agg, histogram, indeks).
2. Domyślny słownik wag + endpoint config wag.
3. Routy multi / time-distribution / oddi + testy API.
4. Recharts + refactor `StatsPanel` na zakładki.
5. Multiselect meczów + wykresy porównawcze.
6. Rozkład czasowy (zależny od osi czasu — `06`/`13`).
7. Krzywa of./def. + edytor wag.

## Kryteria akceptacji
- Wykresy meczu renderują się responsywnie na iPadzie i telefonie.
- Wybór kilku meczów sumuje statystyki i pokazuje trend per mecz.
- Rozkład czasowy pokazuje zdarzenia po kwartach i wewnątrz kwarty.
- Indeks of./def. liczy się wg konfigurowalnych wag i można go zestawić w czasie.

## Zależności
Korzysta z `06` (oś czasu/video) i `13` (game clock, zmiany). Zasila `01` (dashboard) i `11` (MVP).
