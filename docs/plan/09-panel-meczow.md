# 09 — Panel zarządzania meczami + mecz bez składu / skład później

> Pomysły: „Panel zarządzania meczami”, „Można utworzyć mecz i nie dodawać jeszcze składu”.

## Cel
Uporządkować cykl życia meczu: tworzenie (z lub bez składu), edycja, uzupełnianie składu później,
przypisanie do sezonu i kategorii, zakończenie/archiwizacja, ustawienie aktywnego meczu.

## Obecny stan
- `MatchesPanel`: lista + edycja (data/przeciwnik/miejsce/kategoria) + archiwizacja.
- `AdminPanel`: tworzenie meczu wraz ze składem (skład może być pusty — technicznie „mecz bez składu” już działa).
- Backend: `create/edit/end/archive/scores/roster/previous-roster`. Brak osobnego endpointu
  „ustaw/zmień skład istniejącego meczu” inaczej niż przez `previous-roster`/utworzenie.
- `season_id` istnieje w modelu, ale UI go nie ustawia.

## Zakres
**In:** wyraźna ścieżka „Utwórz mecz teraz, skład dodaj później”; edycja składu istniejącego meczu;
przypisanie sezonu; ustawianie aktywnego meczu z listy; statusy (zaplanowany/aktywny/zakończony/zarchiwizowany).
**Out:** statystyki meczu (są w `StatsPanel`/`10`).

## Model danych / decyzje
- Status meczu dziś: `active | ended` (+`archived` bool). Rozważyć dodanie `scheduled` (utworzony, jeszcze nie rozpoczęty),
  by „mecz bez składu / przed startem” był jawny. Migracja wartości statusu (string — bez zmiany schematu, tylko logika).
- Endpoint edycji składu istniejącego meczu: `PUT /v1/clubs/{club_id}/matches/{match_id}/roster`
  (reuse `roster_repo.replace_for_match`).

## Backend (DDD/hexagonal)
- `PUT .../matches/{match_id}/roster` (`CoachOrOwner`) — ustaw/zmień skład po utworzeniu meczu.
- `PUT .../matches/{match_id}` — dołożyć `season_id` i (z `04`) pustą kategorię do edytowalnych pól.
- (Jeśli `scheduled`) `POST .../matches/{match_id}/start` → status `active` + ustawienie jako aktywny w `ClubSettings`.
- Lista meczów: zwracać też `season_id`, liczność składu (`roster_count`) do UI.

## Frontend / UX (iPad-first)
- `AdminPanel`: przycisk „Utwórz bez składu” (pomija sekcję składu) obok „Utwórz mecz”.
- `MatchesPanel`:
  - Karty meczów z statusem, kategorią, sezonem, „skład: N”.
  - Akcje: Ustaw jako aktywny, Edytuj, Edytuj skład (otwiera selektor składu — reuse z AdminPanel),
    Zakończ, Archiwizuj.
  - Filtry: sezon / kategoria / status.
- Wspólny komponent `RosterEditor` używany przy tworzeniu i edycji składu (DRY).
- iPad: lista meczów + panel szczegółów/edycji obok.

## Kroki implementacji
1. Backend: `PUT .../roster`, rozszerzona edycja (`season_id`), opcjonalnie `scheduled`+`start`, `roster_count` w liście.
2. Klient: `api.setRoster`, `api.startMatch`, rozszerzone `editMatch`.
3. Wydzielić `RosterEditor` z `AdminPanel`.
4. `MatchesPanel`: filtry, akcje, edycja składu, ustaw aktywny.
5. Testy: utwórz bez składu → dodaj skład później → rozpocznij/zakończ.

## Kryteria akceptacji
- Można utworzyć mecz bez składu i uzupełnić go później.
- Z listy meczów można ustawić aktywny, edytować skład, zakończyć i zarchiwizować.
- Filtry sezon/kategoria/status działają.

## Zależności
Zależy od `04` (kategoria/pusta) i sezonów. Reuse `RosterEditor` w `AdminPanel`.
