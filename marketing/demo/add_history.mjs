// Adds a handful of FINISHED history matches so the season dashboard (Pulpit)
// looks realistic (record, recent matches, top scorer/assist leaderboards).
// Reuses the squad created by build_demo.mjs. Appends match ids to the artifact.
//
// Run: API=... EMAIL=... PASSWORD=... node add_history.mjs
import { readFileSync, writeFileSync } from 'node:fs';

const API = process.env.API || 'https://api.cap-track.cebo.tech';
const EMAIL = process.env.EMAIL, PASSWORD = process.env.PASSWORD;
if (!EMAIL || !PASSWORD) { console.error('Set EMAIL/PASSWORD'); process.exit(1); }

const artifactUrl = new URL('./demo-artifact.json', import.meta.url);
const artifact = JSON.parse(readFileSync(artifactUrl, 'utf8'));

let token = '';
const clubId = artifact.clubId;
const h = () => ({ 'Content-Type': 'application/json', Authorization: `Bearer ${token}` });
async function j(method, url, body) {
  const res = await fetch(url, { method, headers: h(), body: body != null ? JSON.stringify(body) : undefined });
  const text = await res.text(); let d; try { d = JSON.parse(text); } catch { d = text; }
  if (!res.ok) throw new Error(`${method} ${url} -> ${res.status} ${text}`);
  return d;
}
const club = (p) => `${API}/v1/clubs/${clubId}${p}`;

async function login() {
  const r = await (await fetch(`${API}/v1/auth/login`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email: EMAIL, password: PASSWORD }) })).json();
  token = r.access_token;
  const sel = await j('POST', `${API}/v1/auth/select-club`, { club_id: clubId });
  token = sel.access_token;
}

// History matches: opponent, date, [my, opp] final, scorers {num:goals}, assisters {num:assists}
const HISTORY = [
  { opp: 'AZS Poznań',       date: '2026-05-17', my: 11, opp_s: 9,  goals: { 9: 4, 7: 3, 4: 2, 11: 1, 10: 1 }, assists: { 3: 3, 7: 2, 6: 1 } },
  { opp: 'Posejdon Gdańsk',  date: '2026-05-10', my: 13, opp_s: 13, goals: { 9: 5, 7: 3, 4: 2, 5: 2, 11: 1 }, assists: { 3: 4, 6: 2, 7: 1 } },
  { opp: 'Wisła Kraków',     date: '2026-05-03', my: 16, opp_s: 7,  goals: { 9: 5, 7: 4, 11: 3, 4: 2, 10: 2 }, assists: { 3: 5, 6: 3, 7: 2 } },
  { opp: 'Górnik Radlin',    date: '2026-04-26', my: 12, opp_s: 10, goals: { 9: 4, 7: 3, 4: 3, 5: 1, 10: 1 }, assists: { 3: 3, 7: 2, 6: 2 } },
  { opp: 'Alfa Gorzów',      date: '2026-04-19', my: 8,  opp_s: 12, goals: { 9: 3, 7: 2, 4: 2, 11: 1 },        assists: { 3: 2, 6: 2, 7: 1 } },
];

function cumScores(my, opp) {
  // split a final score into 4 plausible cumulative quarter totals
  const split = (t) => { const a = Math.round(t * 0.28), b = Math.round(t * 0.52), c = Math.round(t * 0.76); return [a, b, c, t]; };
  const m = split(my), o = split(opp);
  return [['1', m[0], o[0]], ['2', m[1], o[1]], ['3', m[2], o[2]], ['4', m[3], o[3]], ['final', my, opp]];
}

async function main() {
  await login();
  const players = await j('GET', club('/players'));
  const byNumber = {}; players.forEach(p => { byNumber[p.number] = { id: p.player_id, name: p.name }; });
  const roster = players.map(p => ({ player_id: p.player_id, number: p.number, name: p.name, team: 'my' }));

  const added = [];
  for (const game of HISTORY) {
    const matchId = `match_${Date.now()}_${Math.floor(Math.random() * 1000)}`;
    await j('POST', club('/matches'), {
      match: { match_id: matchId, date: game.date, opponent: game.opp, place: 'Pływalnia Bytom', age_category: 'U17' },
      roster,
    });
    await j('PUT', club('/settings/active-match'), { match_id: matchId });

    // spread goal & assist events across quarters (all in Q-rotation)
    const evs = [];
    let q = 1;
    for (const [num, n] of Object.entries(game.goals)) for (let i = 0; i < n; i++) { evs.push({ q: ((q++) % 4) + 1, num: +num, flag: 'is_goal_from_play_positional' }); }
    for (const [num, n] of Object.entries(game.assists)) for (let i = 0; i < n; i++) { evs.push({ q: ((q++) % 4) + 1, num: +num, flag: 'is_assist_positional' }); }
    for (const qq of [1, 2, 3, 4]) {
      await j('PUT', club('/settings/quarter'), { quarter: qq });
      const batch = evs.filter(e => e.q === qq).map(e => ({ player_id: byNumber[e.num].id, player_name: byNumber[e.num].name, [e.flag]: 1 }));
      if (batch.length) await j('POST', club('/events'), { events: batch });
    }
    for (const [qk, my, opp] of cumScores(game.my, game.opp_s)) {
      await j('POST', club(`/matches/${matchId}/scores`), { quarter: qk, my_score: my, opp_score: opp });
    }
    await j('POST', club(`/matches/${matchId}/end`)).catch(() => {});
    added.push(matchId);
    console.log(`History: ${game.opp} ${game.my}:${game.opp_s} (${evs.length} events)`);
  }

  // Re-activate the detailed match for the live "Asystent" screenshot.
  await j('PUT', club('/settings/active-match'), { match_id: artifact.matchId });

  artifact.historyMatchIds = added;
  writeFileSync(artifactUrl, JSON.stringify(artifact, null, 2));
  console.log('Added history matches:', added.length, '— detailed match re-activated.');
}

main().catch(e => { console.error('FAILED:', e.message); process.exit(1); });
