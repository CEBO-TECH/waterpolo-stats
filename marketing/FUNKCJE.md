# Cap Track — funkcje aplikacji (materiał do prezentacji)

Bullet-pointy do wykorzystania w prezentacji dla PZPW. Pogrupowane tematycznie —
można brać całe sekcje na osobne slajdy.

---

## 1. Rejestracja meczu na żywo („Asystent")
- **Notowanie akcji jednym tapnięciem** — wybierasz zawodnika i klikasz akcję; zero pisania.
- **Sterowanie głosem** — np. „numer 12 gol z kontrataku"; warstwa AI (Claude) + szybki parser deterministyczny, działa też bez internetu w wersji podstawowej.
- **Tryb pozycyjny / przewaga (man-up)** — każda akcja rozróżnia grę w równowadze i w przewadze/osłabieniu.
- **Skład na żywo: WODA / ŁAWKA** — zmiany jednym kliknięciem, automatyczne liczenie **czasu gry** każdego zawodnika.
- **Wynik na bieżąco** — punktacja po każdej kwarcie, automatyczny wynik końcowy.
- **Cofnij / popraw** — błędną akcję cofasz jednym przyciskiem; pełna lista ostatnich zdarzeń.
- **Praca offline-first** — akcje zapisują się lokalnie i synchronizują automatycznie po odzyskaniu sieci (kluczowe na pływalniach ze słabym zasięgiem).

## 2. Statystyki waterpolo (dedykowane dyscyplinie)
- **Bogata taksonomia akcji** specyficzna dla piłki wodnej, m.in.:
  - gole: z gry, z kontrataku, z centra, z rzutu 5 m, z karnego;
  - asysty, obrony bramkarza, niecelne rzuty i straty (złe podanie, strata 1:1, przekroczenie 30 s);
  - sprowokowane i popełnione wykluczenia oraz karne (w polu / z centra);
  - obrona: przejęcia, bloki, brak powrotu, obrony w osłabieniu.
- **Tabela per zawodnik** — wszystkie akcje w rozbiciu na kwarty (Q1–Q4) i całość meczu.
- **Wykresy** — dynamika goli i strat w czasie meczu, udział zawodników.
- **Porównywanie meczów** — zestawianie wielu spotkań obok siebie.
- **Trend zawodnika** — forma w kolejnych meczach.
- **Filtry** — kategoria wiekowa, zakres dat, konkretny zawodnik, wybór meczów.
- **Agregacja po zawodniku (ID), nie po numerze** — statystyki są poprawne nawet gdy zawodnik zmienia numer między meczami.

## 3. Synchronizacja z wideo (YouTube)
- **Każda akcja ma znacznik czasu** — z poziomu statystyk przeskakujesz do dokładnego momentu w nagraniu meczu.
- **Automatyczne wykrycie startu transmisji** (YouTube Data API) — albo ręczne ustawienie „start = teraz".
- **Analiza po meczu** — trener i zawodnik oglądają konkretne zagrania bez przewijania całego nagrania.

## 4. MVP i podsumowanie meczu
- **Automatyczna propozycja MVP** — ranking zawodników wg punktów za akcje.
- **Zatwierdzenie MVP** jednym kliknięciem; pełny ranking widoczny dla zespołu.

## 5. Pulpit sezonu
- **Skrót sezonu** — bilans (zwycięstwa / porażki / remisy), bramki zdobyte i stracone, różnica.
- **Ostatnie mecze** z wynikami i rezultatem.
- **Rankingi** — najlepsi strzelcy i asystenci.
- **Filtr po kategorii wiekowej** — osobny obraz dla Seniorów, U19, U17, U15 itd.

## 6. Zarządzanie zespołem
- **Kartoteka zawodników** — profil, rok urodzenia, przynależność do kategorii.
- **Słownik kategorii wiekowych** per klub (własne grupy).
- **Składy meczowe** z numerami nadawanymi na dany mecz; podpowiedź składu z poprzedniego meczu.
- **Sezony** — grupowanie meczów i statystyk w ramach sezonu.
- **Notatki głosowe do meczu** — krótkie nagrania audio (np. uwagi trenera) przypięte do spotkania.

## 7. Konta, kluby i role (multi-tenant)
- **Wiele klubów** na jednym koncie; przełączanie kontekstu klubu.
- **Role i uprawnienia** — Właściciel, Trener, Zawodnik.
- **Zapraszanie członków** i zarządzanie dostępem (zaproszenia, członkowie).
- **Widok zawodnika (self-service)** — zawodnik widzi własne statystyki i mecze, bez dostępu do panelu zarządzania.

## 8. Aplikacja mobilna i platforma
- **Natywne aplikacje iOS i Android** (Capacitor) obok wersji webowej — jedna baza kodu.
- **Rozpoznawanie mowy natywnie** na urządzeniu (wtyczka speech-recognition).
- **Projektowane pod iPada** — główny scenariusz: trener z tabletem przy basenie.
- **Architektura klient–API** — szybki frontend + samodzielne API (FastAPI), gotowe pod integracje.

## 9. Bezpieczeństwo i niezawodność
- **Uwierzytelnianie tokenowe** (access + refresh), izolacja danych per klub.
- **Offline-first z kolejką synchronizacji** — żadna akcja meczowa nie ginie przy utracie sieci.
- **Własny hosting** (Coolify/Docker, Postgres, S3/MinIO na audio) — pełna kontrola nad danymi klubów.

---

### Hasła-skróty na slajd tytułowy / podsumowanie
- Rejestracja na żywo • Statystyki dedykowane waterpolo • Wideo • AI/głos • Aplikacja mobilna
- „Koniec statystyk na kartce" — jeden tablet zamiast zeszytu, Excela i pamięci trenera.
- Dane spójne, natychmiastowe i powiązane z nagraniem meczu.
