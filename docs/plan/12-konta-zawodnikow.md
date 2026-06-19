# 12 — Konta zawodników + rocznik + logowanie zawodnika

> Pomysł: „Rozważyć, żeby wprowadzając zawodników od razu tworzyć im konta i uzupełniać rocznik —
> wtedy będą mogli się logować i sprawdzać mecze, w których grali”.

## Cel
Powiązać zawodnika (`Player`) z kontem (`User`/`ClubMembership` rola PLAYER), dodać rocznik (data/rok urodzenia),
i dać zawodnikowi widok „moje mecze / moje statystyki” po zalogowaniu.

## Obecny stan
- `Player` i `User` są **rozłączne** — brak powiązania `player_id ↔ user_id`.
- Rola `PLAYER` istnieje, ale nie ma przepływu zakładania konta zawodnika ani jego widoku.
- `Player` nie ma pola rocznika/daty urodzenia.
- `player_profile_service` już liczy statystyki per zawodnik (gotowe do widoku zawodnika).

## Model danych / decyzje
- Dodać do `Player`: `birth_year` (lub `birth_date`), `email?`, `user_id?` (powiązanie z kontem). Migracja.
- **Tworzenie konta przy dodawaniu zawodnika (opcjonalne):** jeśli podano email →
  utwórz `User` (lub podłącz istniejący) + `ClubMembership(role=PLAYER)` + ustaw `Player.user_id`.
  Reuse mechanizmu zaproszeń z `07` (zawodnik dostaje link, ustawia hasło).
- **Widok zawodnika:** PLAYER widzi tylko swoje dane (mecze, w których był w składzie + swoje statystyki),
  nie panele zarządzania.

## Backend (DDD/hexagonal)
- Migracja `players`: `birth_year`, `email`, `user_id`.
- `domain/services/player_account_service.py` — `link_or_create_account(player, email, role=PLAYER)`:
  tworzy/łączy `User`, dodaje membership, ustawia `Player.user_id`; reguły (duplikaty, istniejące konto).
- Endpointy:
  - rozszerzyć `POST/PUT /players` o `birth_year`, `email`, flagę „utwórz konto”.
  - `GET /v1/clubs/{club_id}/me/player` → zawodnik powiązany z bieżącym userem.
  - `GET /v1/clubs/{club_id}/me/matches` → mecze, w których zawodnik był w składzie (po `match_roster.player_id`).
  - guardy: PLAYER ma dostęp tylko do „swoich” zasobów.
- Reuse `player_profile` dla statystyk zawodnika.

## Frontend / UX (iPad-first)
- `PlayersPanel` (z `08`): pola `rocznik` i `email` + checkbox „Utwórz konto / wyślij zaproszenie”.
- **Tryb zawodnika:** po zalogowaniu konta z rolą PLAYER → uproszczony interfejs:
  Dashboard zawodnika (moje KPI/trend), „Moje mecze” (lista + szczegóły, w których grał), profil.
  Ukryte: zarządzanie, asystent (chyba że COACH/OWNER).
- iPad-first: karty meczów + profil obok; duże, czytelne KPI.

## Kroki implementacji
1. Migracja `players` (birth_year/email/user_id).
2. `player_account_service` (link/create) + reuse zaproszeń `07` + testy.
3. Rozszerzenie endpointów `players` + `me/player` + `me/matches` + guardy roli PLAYER.
4. UI dodawania zawodnika z kontem/rocznikiem.
5. Tryb zawodnika (dashboard + moje mecze + profil) z ograniczeniami widoczności.

## Kryteria akceptacji
- Dodając zawodnika można podać rocznik i (opcjonalnie) utworzyć mu konto/zaproszenie.
- Zawodnik loguje się i widzi tylko swoje mecze i statystyki.
- Powiązanie `Player.user_id` jest spójne; PLAYER nie ma dostępu do paneli zarządzania.

## Zależności
Bazuje na `07` (zaproszenia/role) i `08` (panel zawodników). Widok korzysta z `player_profile`/`10`.
