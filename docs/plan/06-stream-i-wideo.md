# 06 — Link do streamu + znaczniki wideo

> Pomysł: „Wklejanie linku do streama”.

## Cel
Podpiąć do meczu link do transmisji (YouTube/stream), a każdą rejestrowaną akcję znaczyć
timestampem wideo — żeby później jednym kliknięciem skoczyć do momentu akcji w nagraniu.

## Obecny stan
- Backend **gotowy w dużej części**: encja `YouTubeStream` (`youtube_url`, `video_id`, `stream_start_time`),
  serwis `youtube_service`, route `youtube.py` (`POST/GET .../matches/{match_id}/youtube`),
  `Event.video_timestamp` (sekundy) + kolumna w DB. `api.attachYouTube` / `api.getYouTube` w kliencie.
- **Brak UI** do wklejenia linku i **brak** wyliczania/zapisywania `video_timestamp` przy tworzeniu eventu.
- Bootstrap zwraca `youtube` dla aktywnego meczu, ale front tego nie używa.

## Zakres
**In:** UI wklejania linku + ustawienie „startu streamu”; automatyczne liczenie `video_timestamp` przy zapisie akcji;
odtwarzacz/skok do momentu z poziomu listy akcji i tabeli statystyk.
**Out:** synchronizacja z innymi platformami niż YouTube/proste pliki (faza 2).

## Backend (DDD/hexagonal)
- W większości reuse. Upewnić się, że `youtube_service` poprawnie ekstrahuje `video_id` i liczy offset
  względem `stream_start_time`.
- Rozszerzyć tworzenie eventu: jeśli mecz ma stream ze `stream_start_time`, backend (lub front) wylicza
  `video_timestamp = now - stream_start_time` (sek.). Rekomendacja: liczyć po stronie backendu w
  `event_service` na podstawie aktualnego streamu, by była jedna prawda.
- Zwracać `video_timestamp` w `GET .../events` (lista ostatnich akcji) i w odpowiedziach statystyk, gdzie sensowne.

## Frontend / UX (iPad-first)
- W `MatchesPanel`/`AdminPanel` (i nagłówku meczu) pole „Link do transmisji” + przycisk „Ustaw start streamu = teraz”
  (zapisuje `stream_start_time`) → `api.attachYouTube`.
- `ScoreKeeper`: gdy mecz ma stream, każdy zapis akcji niesie `video_timestamp` (z backendu lub liczony lokalnie).
- Lista „Ostatnie akcje” i tabela statystyk: ikonka ▶ przy akcji → otwiera odtwarzacz w danej sekundzie
  (YouTube IFrame API `start=` / `seekTo`), na iPadzie panel boczny lub modal z playerem.
- Wskaźnik „stream podpięty / start ustawiony” w headerze meczu.

## Kroki implementacji
1. UI wklejania linku + „ustaw start” (web + mobile) + walidacja URL.
2. Liczenie `video_timestamp` przy evencie (decyzja: backend `event_service` vs front) + zwracanie w listach.
3. Komponent `VideoPlayer` (YouTube IFrame) + „skocz do sekundy”.
4. Przyciski ▶ w liście akcji i statystykach.
5. Test: akcja zapisana 65 s po starcie streamu ma `video_timestamp≈65` i skok działa.

## Kryteria akceptacji
- Można wkleić link i ustawić start streamu dla meczu.
- Nowe akcje zapisują `video_timestamp`.
- Z listy akcji/statystyk otwiera się wideo w momencie akcji.

## Zależności
Samodzielne (backend gotowy). Wzbogaca `10` (rozkład czasowy) i `ScoreKeeper`.
