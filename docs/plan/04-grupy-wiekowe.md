# 04 — Grupy wiekowe (kategorie) — zawodnicy, mecze, auto-skład

> Pomysły: „Globalni zawodnicy per klub ale przypisani do grup (kategorie wiekowe)”,
> „Każdy mecz przypisany per grupa wiekowa”, „Może być mecz bez grupy wiekowej”,
> „Tworzymy nowy mecz, wybieramy grupę wiekową i od razu pokazują się zawodnicy”.

## Cel
Zawodnik jest globalny w klubie, ale przypisany do jednej lub wielu **grup (kategorii wiekowych)**.
Mecz ma kategorię (lub jej nie ma). Przy tworzeniu meczu wybór kategorii **od razu** podpowiada skład z tej grupy.

## Obecny stan
- Model **jest**: `PlayerAgeCategory` (junction player↔kategoria), `Match.age_category` (string, domyślnie „Seniorzy”).
- Endpointy `GET/PUT /players/{player_id}/age-categories` istnieją; brak UI.
- `AdminPanel` pokazuje **wszystkich** zawodników klubu (bez filtra po kategorii); kategoria meczu to zwykły select.
- „Mecz bez grupy” niewspierany — `age_category` ma default „Seniorzy”, nie ma opcji pustej.

## Zakres
**In:** zarządzanie kategoriami zawodnika (UI), słownik kategorii klubu, filtr składu po kategorii w „Nowy mecz”,
auto-podpowiedź składu, obsługa meczu „bez kategorii”.
**Out:** statystyki filtrowane po kategorii w analizie (→ `10`), choć dane będą gotowe.

## Model danych / decyzje
- **Słownik kategorii per klub.** Dziś kategorie to wolny string. Proponowane: encja `AgeCategory`
  (`id`, `club_id`, `name`, `sort_order`) — by każdy klub miał własną listę (U11/U13/U15/U17/U19/Seniorzy…).
  Mniejszy wariant (mniej pracy): trzymać stałą listę w configu klubu (`ClubConfig`). Rekomendacja: osobna encja + migracja.
- **Mecz bez kategorii:** dopuścić `age_category = ""`/`NULL` i etykietę „Bez kategorii” w UI.
  `MatchModel.age_category` już istnieje — zmienić default na pusty lub dodać nullable; migracja.

## Backend (DDD/hexagonal)
- `domain/models/age_category.py` — `AgeCategory` (jeśli wybieramy encję).
- Port `AgeCategoryRepository` w `domain/ports/repositories.py` + adapter w `adapters/persistence/repositories/`.
- `api/routes/age_categories.py` → CRUD `/v1/clubs/{club_id}/age-categories` (`CoachOrOwner` do zmian, `AnyMember` GET).
- Rozszerzyć `players` repo/route: zwracać kategorie zawodnika w liście (lub endpoint
  `GET /players?age_category=U17` filtrujący po junction) — potrzebne do auto-składu.
- `matches`: zezwolić na pustą kategorię (walidacja + migracja default).

## Frontend / UX (iPad-first)
- **PlayersPanel (`08`):** przy zawodniku multi-select chipów kategorii (zapis `PUT age-categories`).
- **AdminPanel „Nowy mecz”:** po wyborze kategorii lista zawodników **filtruje się** do tej grupy i skład
  zaznacza się automatycznie (auto-podpowiedź); użytkownik może odznaczyć/dodać spoza grupy.
  Opcja „Bez kategorii” → pokazuje wszystkich.
- Słownik kategorii edytowalny w ustawieniach klubu (lista chipów + dodaj/usuń/kolejność).
- iPad: dwukolumnowo (lewa: filtr+lista zawodników, prawa: podgląd składu).

## Kroki implementacji
1. (Jeśli encja) model `AgeCategory` + port + adapter + migracja + seed domyślnych kategorii przy tworzeniu klubu.
2. Route CRUD kategorii + testy.
3. Filtr `GET /players?age_category=` (po junction) + test.
4. Migracja: `Match.age_category` dopuszcza pustą wartość; walidacja w route.
5. UI: chipy kategorii w PlayersPanel; auto-skład + filtr w AdminPanel; ekran słownika kategorii.

## Kryteria akceptacji
- Zawodnika można przypisać do wielu kategorii; widać je w panelu zawodników.
- Wybór kategorii w „Nowy mecz” natychmiast filtruje i podpowiada skład.
- Można utworzyć mecz „Bez kategorii”.

## Zależności
Zależy od `08` (panel zawodników jako miejsce przypisań). Wymagane przez `09`, `10`, `01` (filtry).
