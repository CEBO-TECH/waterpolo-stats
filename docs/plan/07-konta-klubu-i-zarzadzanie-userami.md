# 07 — Wiele kont per klub + panel zarządzania użytkownikami

> Pomysły: „Wiele kont per klub (założyciel dodaje)”, „Panel zarządzania userami”.

## Cel
Założyciel (OWNER) zarządza dostępem do klubu: zaprasza/dodaje konta (trener/zawodnik), nadaje role,
odbiera dostęp. Widok listy członków klubu z rolami.

## Obecny stan
- Role: `OWNER | COACH | PLAYER` (`UserRole`), encja `ClubMembership`.
- Jest `POST /v1/clubs/{club_id}/invite` (OWNER) — ale wymaga, by zapraszany **już miał konto** (po emailu).
- Brak: listy członków, zmiany roli, usunięcia członka, zaproszeń dla nieistniejących kont.
- Brak UI.

## Zakres
**In:** panel „Użytkownicy” (lista członków + role), zapraszanie po emailu (z obsługą konta nieistniejącego),
zmiana roli, usunięcie z klubu. Widoczny tylko dla OWNER (i podgląd dla COACH).
**Out:** logowanie/konta zawodników jako osobny przepływ samoobsługi (→ `12`).

## Backend (DDD/hexagonal)
- Rozszerzyć `user_repo` / route `clubs.py`:
  - `GET /v1/clubs/{club_id}/members` (OWNER/COACH) → lista `{user_id, email, role, created_at}`.
  - `PATCH /v1/clubs/{club_id}/members/{user_id}` (OWNER) → zmiana roli.
  - `DELETE /v1/clubs/{club_id}/members/{user_id}` (OWNER) → usunięcie członkostwa (nie można usunąć ostatniego OWNERa).
- **Zaproszenia dla nieistniejących kont:** encja `ClubInvitation`
  (`id`, `club_id`, `email`, `role`, `token`, `status` [pending|accepted|revoked], `expires_at`, `created_by`).
  Endpointy: `POST .../invitations`, `GET .../invitations`, `POST /v1/invitations/{token}/accept` (po rejestracji/loginie).
  Wysyłka maila przez `NotificationPort` (adapter email) lub na start: zwracać link do skopiowania.
- Reguły w `domain/services/membership_service.py` (walidacja: ostatni owner, duplikaty, własna rola).
- Migracja `club_invitations`.

## Frontend / UX (iPad-first)
- Nowy tryb/komponent `UsersPanel.tsx` (pozycja w menu „Zarządzanie”, widoczna dla OWNER/COACH).
- Lista członków: email, chip roli (kolory), akcje (zmień rolę / usuń) — tylko OWNER.
- Formularz „Zaproś”: email + rola; jeśli konto istnieje → od razu dodaj; jeśli nie → utwórz zaproszenie i pokaż link.
- Sekcja „Oczekujące zaproszenia” z możliwością cofnięcia.
- iPad: tabela/karty 2-kolumnowo; duże przyciski akcji.

## Kroki implementacji
1. Endpointy members (list/patch/delete) + reguły w serwisie + testy.
2. Encja `ClubInvitation` + migracja + endpointy zaproszeń + accept.
3. (Opcjonalnie) adapter email; na start link do skopiowania.
4. `UsersPanel` + integracja z rolami w UI.
5. Test: OWNER dodaje COACH-a, zmienia rolę, usuwa; PLAYER nie widzi panelu.

## Kryteria akceptacji
- OWNER widzi listę członków i zarządza rolami/dostępem.
- Zaproszenie działa zarówno dla istniejącego konta, jak i nowego (przez link/token).
- Nie można usunąć/odebrać roli ostatniemu OWNERowi.

## Zależności
Bazuje na rolach z `deps.py`. Powiązane z `03` (kontekst klubu) i `12` (konta zawodników).
