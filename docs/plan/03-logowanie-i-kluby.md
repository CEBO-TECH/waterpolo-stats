# 03 — Logowanie i przełączanie klubów

> Pomysł: „Logowanie per klub”.

## Cel
Poprawny przepływ logowania, gdy użytkownik należy do jednego lub wielu klubów: wybór klubu po zalogowaniu,
przełącznik klubu w aplikacji, token i kontekst zawsze spięte z aktywnym klubem.

## Obecny stan
- Logowanie działa (`/v1/auth/login` → access+refresh; `/auth/me` zwraca `clubs[]`).
- `LoginPage` po loginie automatycznie ustawia `club_id = me.clubs[0]` (`api.setClubId`). Brak wyboru, gdy klubów > 1.
- Token JWT koduje `club_id` i `role` **pierwszego** członkostwa (`auth.py: login`) — przy wielu klubach to błąd.
- Brak UI przełączania klubu; `club_id` siedzi w `localStorage`.

## Zakres
**In:** ekran/krok wyboru klubu, gdy `clubs.length > 1`; przełącznik klubu w headerze/menu;
re-issue tokena pod wybrany klub; spójność `role` w UI z wybranym klubem.
**Out:** zapraszanie do klubu i zarządzanie userami (→ `07`).

## Backend (DDD/hexagonal)
Token musi odpowiadać aktywnemu klubowi:
- Dodać `POST /v1/auth/select-club` (body `{club_id}`, guard: zalogowany) → weryfikuje członkostwo
  (`user_repo.get_membership`) i zwraca **nowy** `access_token` z właściwym `club_id`+`role`.
  (Alternatywa: `club_id` jako parametr przy wymianie refresh-tokena.)
- `auth_service` (`domain/services/auth_service.py`) — metoda `issue_for_club(user, membership)` budująca claims (logika domenowa).
- `/auth/login` zostaje, ale gdy klubów wiele, front nie ufa domyślnemu `club_id` — wymusza select-club.

## Frontend / UX (iPad-first)
- `LoginPage`: po `login()` pobrać `me`; jeśli `clubs.length === 1` → auto-select + `selectClub`; jeśli > 1 →
  ekran „Wybierz klub” (duże karty klubów, iPad-first siatka).
- Przełącznik klubu: w `AppNav`/headerze (`02`) menu z nazwą klubu i rolą; zmiana → `api.selectClub(clubId)` →
  zapis nowego tokena + `club_id` → `bootstrap()`.
- `api.selectClub(clubId)` w `lib/api.ts` (zapis `access_token` i `club_id`). Rola z `bootstrap.user.role` steruje widocznością akcji.
- Jeśli `clubs.length === 0` (świeże konto) → ekran „Utwórz klub” (reuse `createClub`).

## Kroki implementacji
1. Backend: `select-club` route + `auth_service.issue_for_club` + test.
2. `api.selectClub` w kliencie.
3. `LoginPage`: obsługa 0 / 1 / wiele klubów.
4. Przełącznik klubu w nawigacji (po `02`).
5. Test: użytkownik w 2 klubach widzi dane właściwego klubu po przełączeniu.

## Kryteria akceptacji
- Użytkownik z wieloma klubami wybiera klub; token i dane dotyczą wybranego klubu.
- Przełączenie klubu w aplikacji odświeża cały stan (bootstrap) bez przelogowania.
- Rola w UI (ukrywanie akcji COACH/OWNER vs PLAYER) zgadza się z wybranym klubem.

## Zależności
Współgra z `02` (miejsce na przełącznik) i `07` (członkostwa). Może iść zaraz po `02`.
