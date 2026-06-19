# 11 — Sugerowanie MVP po zakończeniu meczu

> Pomysł: „Sugerowanie MVP po zakończeniu meczu”.

## Cel
Po zakończeniu meczu aplikacja proponuje MVP (i ranking 2–3 najlepszych) na podstawie statystyk,
z czytelnym uzasadnieniem („dlaczego ten zawodnik”).

## Obecny stan
- Brak jakiejkolwiek logiki MVP.
- Jest moment zakończenia meczu (`endMatch` → popup) — naturalny trigger.
- Dane: per-player flagi z `stats_service`/`player_profile_service`; wagi of./def. z `10`.

## Decyzje projektowe
- **Scoring MVP** = ważona suma wkładu zawodnika: + gole/asysty/sprowokowania/przejęcia/bloki/skuteczność,
  − straty/błędy/wykluczenia/karne spowodowane. Reuse słownika wag z `10` (`stat_weights`) + osobne wagi „MVP”
  (lub te same). Normalizacja względem czasu gry, gdy dostępne (`13`).
- Wynik: ranking z `score` i rozbiciem składników (do uzasadnienia).

## Backend (DDD/hexagonal)
- `domain/services/mvp_service.py` — `compute_mvp(events, roster, weights) -> [{player_id, name, score, breakdown}]`.
  Czysta logika domenowa, testowalna.
- Route: `GET /v1/clubs/{club_id}/matches/{match_id}/mvp` (`AnyMember`).
- (Opcjonalnie) zapis wyboru: pole `mvp_player_id` na `Match` (trener może zatwierdzić/zmienić sugestię) — migracja.

## Frontend / UX (iPad-first)
- Po `endMatch`: zamiast/obok obecnego popupu — ekran „Podsumowanie meczu” z sugerowanym MVP:
  duża karta zawodnika, score, top składniki (np. „3 gole, 2 asysty, 80% skuteczności”), podium 2–3 miejsc.
- Trener może „Zatwierdź MVP” lub wybrać innego (zapis `mvp_player_id`).
- MVP pokazywane też w szczegółach meczu i (opcjonalnie) na dashboardzie.
- iPad: karta MVP + podium obok skróconych statystyk.

## Kroki implementacji
1. `mvp_service` + testy (różne profile zawodników).
2. Route `/mvp` + (opcjonalnie) zapis `mvp_player_id` + migracja.
3. Ekran „Podsumowanie meczu” po zakończeniu + zatwierdzanie MVP.
4. Wyświetlanie MVP w szczegółach meczu/dashboardzie.

## Kryteria akceptacji
- Po zakończeniu meczu pojawia się sugerowany MVP z uzasadnieniem.
- Trener może zatwierdzić lub zmienić MVP, a wybór jest zapisany.
- Scoring jest spójny z wagami of./def.

## Zależności
Zależy od `10` (wagi/agregacja) i pośrednio `13` (normalizacja per czas gry). Trigger: zakończenie meczu (`09`).
