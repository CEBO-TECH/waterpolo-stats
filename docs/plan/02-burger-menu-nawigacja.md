# 02 — Burger menu + nawigacja (iPad-first)

> Pomysł: „Burger menu”.

## Cel
Czytelna, spójna nawigacja między sekcjami aplikacji, działająca tak samo dobrze na iPadzie i telefonie,
zamiast obecnego ciasnego paska przycisków w headerze.

## Obecny stan
- `app/page.tsx` renderuje wszystkie tryby jako przyciski **inline** w `<header>` (zawijają się, ciasno na telefonie).
- Drawer (menu boczne) **istnieje**, ale przycisk burgera ma `style={{ display: 'none' }}` (linia ~278) — nigdy nie widać.
- Tryby: `score | stats | players | matches | admin` (`Mode` w `lib/types.ts`).

## Zakres
**In:** widoczny przycisk burgera; drawer jako główne menu; responsywne przełączanie
(iPad: stały pasek boczny lub górny segmented; telefon: burger + drawer); aktywny stan; sekcje pogrupowane.
**Out:** nowe ekrany (dodawane w innych planach — menu ma być rozszerzalne).

## Backend
Brak zmian.

## Frontend / UX (iPad-first)
- Wydzielić nawigację z `page.tsx` do `components/AppNav.tsx` (źródło prawdy: lista `MODES`, już dodatkowo
  rozszerzona o `dashboard`).
- **iPad (≥1024px):** lewy stały sidebar nawigacyjny (ikona + label) albo górny segmented control — duże cele dotykowe.
- **Telefon (<768px):** widoczny burger `☰` w headerze → otwiera istniejący `.drawer` (usuń `display:none`).
- Grupowanie pozycji w drawerze: *Mecz na żywo* (Asystent), *Analiza* (Dashboard, Statystyki),
  *Zarządzanie* (Zawodnicy, Mecze, Użytkownicy, Nowy mecz). Sekcje przygotowane pod kolejne plany.
- Dodać ikony (lekki zestaw SVG inline lub `lucide-react`), aktywny stan = `--accent`.
- Drawer: zamykanie po wyborze, overlay, `Esc`, focus-trap (a11y), szer. ~280px.

## Kroki implementacji
1. `components/AppNav.tsx` (sidebar/segmented dla tabletu) + `components/Drawer.tsx` (telefon) lub jeden komponent z media-query.
2. Przenieść `MODES` i logikę `setMode` do propsów; usunąć `display:none` z burgera.
3. CSS w `globals.css`: `@media (min-width:1024px)` sidebar; `<768px` burger+drawer; ukryć inline-bar na telefonie.
4. Dodać ikony i grupy sekcji.
5. Sanity-check na szerokościach 1366 / 1024 / 768 / 390.

## Kryteria akceptacji
- Na iPadzie nawigacja stale widoczna (sidebar/segmented), bez zawijania.
- Na telefonie burger otwiera drawer; po wyborze sekcji drawer się zamyka.
- Aktywna sekcja wyróżniona; nawigacja klawiaturą i `Esc` działają.

## Zależności
Brak. Fundament UX — warto zrobić pierwsze, bo kolejne ekrany dokładają pozycje do menu.
