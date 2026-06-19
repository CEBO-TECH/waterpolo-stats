# 08 — Panel zarządzania zawodnikami (rozbudowa)

> Pomysł: „Panel zarządzania zawodnikami”.

## Cel
Pełny panel zawodników klubu: dodawanie, edycja, usuwanie, przypisanie do kategorii wiekowych,
podgląd profilu/statystyk, wyszukiwanie i sortowanie — wygodny na iPadzie.

## Obecny stan
- `PlayersPanel` umożliwia tylko **dodanie** (numer + imię) i **usunięcie**. Brak edycji, kategorii, profilu, wyszukiwarki.
- Backend: `GET/POST/DELETE /players`, `GET/PUT /players/{id}/age-categories`, `GET /players/{id}/stats` (profil + trend).
- Brak endpointu **edycji** zawodnika (`PUT /players/{id}`).

## Zakres
**In:** edycja zawodnika, wyszukiwanie/sortowanie, chipy kategorii wiekowych (spięte z `04`),
wejście w profil zawodnika (statystyki/trend z `player_profile`).
**Out:** zakładanie kont/rocznik zawodnika (→ `12`); wykresy w profilu (→ `10`).

## Backend (DDD/hexagonal)
- Dodać `PUT /v1/clubs/{club_id}/players/{player_id}` (`CoachOrOwner`) — edycja `number`, `name`, `team`.
  Repo: `update_fields` analogicznie do match repo.
- Reuse `age-categories` i `players/{id}/stats`.
- (Walidacja) ostrzeżenie/blokada usunięcia, gdy zawodnik ma zdarzenia — dziś delete kasuje kaskadowo (informować w UI).

## Frontend / UX (iPad-first)
- Przebudowa `PlayersPanel`:
  - Górny pasek: szukaj + filtr kategorii + sort (numer/nazwisko).
  - Lista/karty zawodników: numer, imię, chipy kategorii; akcje Edytuj / Profil / Usuń.
  - Popup edycji (numer, imię, drużyna, kategorie — multi-select chipów).
  - „Profil” → komponent `PlayerProfile` (KPI: mecze, gole, skuteczność, asysty, straty…; trend listą,
    a wykresy dochodzą w `10`).
- iPad: dwukolumnowo (lewa lista, prawa profil/edycja). Telefon: lista → wejście w profil pełnoekranowo.

## Kroki implementacji
1. Backend `PUT /players/{id}` + test.
2. `api.updatePlayer`, `api.getPlayerProfile` (już jest) w kliencie.
3. Refactor `PlayersPanel` (szukaj/sort/filtr + akcje + popup edycji).
4. Chipy kategorii (po `04`).
5. Komponent `PlayerProfile` (KPI + trend).

## Kryteria akceptacji
- Można dodać/edytować/usunąć zawodnika i przypisać kategorie.
- Wyszukiwarka i sort działają; profil pokazuje statystyki z `player_profile`.
- Na iPadzie lista + profil obok siebie.

## Zależności
Fundament dla `04` (przypisania kategorii). Profil korzysta z istniejącego `player_profile_service`; wykresy → `10`.
