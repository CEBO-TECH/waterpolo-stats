// Removes every demo object created for the screenshots, returning the club to
// an empty state. Matches have no hard-delete endpoint, so they are archived
// (excluded from bootstrap/list/dashboard/stats); players are hard-deleted.
//
// Run: API=... EMAIL=... PASSWORD=... node cleanup.mjs
import { readFileSync } from 'node:fs';

const API = process.env.API || 'https://api.cap-track.cebo.tech';
const EMAIL = process.env.EMAIL, PASSWORD = process.env.PASSWORD;
if (!EMAIL || !PASSWORD) { console.error('Set EMAIL/PASSWORD'); process.exit(1); }

const artifact = JSON.parse(readFileSync(new URL('./demo-artifact.json', import.meta.url), 'utf8'));
const clubId = artifact.clubId;
let token = '';
const h = () => ({ 'Content-Type': 'application/json', Authorization: `Bearer ${token}` });
async function call(method, url, body) {
  const res = await fetch(url, { method, headers: h(), body: body != null ? JSON.stringify(body) : undefined });
  return res.status;
}
const club = (p) => `${API}/v1/clubs/${clubId}${p}`;

async function login() {
  const r = await (await fetch(`${API}/v1/auth/login`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email: EMAIL, password: PASSWORD }) })).json();
  token = r.access_token;
  const sel = await (await fetch(`${API}/v1/auth/select-club`, { method: 'POST', headers: h(), body: JSON.stringify({ club_id: clubId }) })).json();
  token = sel.access_token;
}

async function main() {
  await login();

  // 1) Clear active match so nothing references the demo match.
  console.log('clear active match:', await call('PUT', club('/settings/active-match'), { match_id: '' }));

  // 2) Archive all demo matches.
  const matchIds = [artifact.matchId, ...(artifact.historyMatchIds || [])].filter(Boolean);
  for (const mid of matchIds) {
    console.log('archive', mid, '->', await call('POST', club(`/matches/${mid}/archive`)));
  }

  // 3) Delete all demo players. player_age_categories has a FK without ON DELETE
  //    CASCADE, so clear each player's categories first or the delete 500s.
  //    (events have no player FK; roster + substitutions cascade automatically.)
  let ids = artifact.playerIds || [];
  try {
    const players = await (await fetch(club('/players'), { headers: h() })).json();
    if (Array.isArray(players) && players.length) ids = players.map(p => p.player_id);
  } catch {}
  for (const pid of ids) {
    await call('PUT', club(`/players/${pid}/age-categories`), { categories: [] });
    console.log('delete player', pid, '->', await call('DELETE', club(`/players/${pid}`)));
  }

  // 4) Verify empty.
  const boot = await (await fetch(club(`/bootstrap?t=${Date.now()}`), { headers: h() })).json();
  console.log(`VERIFY -> players: ${(boot.players || []).length}, matches: ${(boot.matches || []).length}`);
}

main().catch(e => { console.error('CLEANUP FAILED:', e.message); process.exit(1); });
