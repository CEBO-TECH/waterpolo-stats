# Screeny do prezentacji — pipeline

Generuje **prawdziwe** screeny aplikacji do `marketing/screens/` (osadzane potem
w `marketing/Cap-Track-PZPW.pptx` przez `marketing/generate_deck.py`).

Konto produkcyjne bywa puste, więc pipeline tworzy realistyczne dane demo,
robi screeny i sprząta po sobie (klub wraca do pustego stanu).

## Wymagania
- Node 18+ i `npm install` w tym katalogu (instaluje `puppeteer-core`).
- Zainstalowany Google Chrome (`/Applications/Google Chrome.app`).
- Uruchomiony frontend dev-server na `:3001` wskazujący na prod API
  (`frontend/.env.local` → `NEXT_PUBLIC_API_URL=https://api.cap-track.cebo.tech`).

## Kroki
```bash
cd marketing/demo
npm install
export API=https://api.cap-track.cebo.tech EMAIL=<login> PASSWORD=<hasło>

node build_demo.mjs    # skład + 1 szczegółowy mecz (zostaje aktywny)
node add_history.mjs   # kilka zakończonych meczów → bogaty Pulpit
node capture.mjs       # 4 PNG do ../screens/ (pulpit, stats, asystent, mvp)
node cleanup.mjs       # usuwa dane demo (klub → pusty)

cd .. && python3 generate_deck.py   # przebudowa .pptx z nowymi screenami
```

`demo-artifact.json` (clubId / matchId / playerIds) jest zapisywany przez
`build_demo.mjs` i używany przez `cleanup.mjs`. Hasło podawaj przez zmienną
środowiskową — nie commituj go.

Haczyki backendu opisane w pamięci projektu (`marketing-deck-screens`):
wyniki kwart narastające; mecz ma tylko archiwizację (brak hard-delete);
usunięcie zawodnika wymaga wpierw wyczyszczenia jego kategorii wiekowych.
