// Builds realistic demo data in the real club so we can capture genuine app
// screenshots for the deck, then writes an artifact listing every created id so
// cleanup.mjs can remove it all afterwards (club returns to empty).
//
// Run:  API=https://api.cap-track.cebo.tech EMAIL=... PASSWORD=... node build_demo.mjs
import { writeFileSync } from 'node:fs';

const API = process.env.API || 'https://api.cap-track.cebo.tech';
const EMAIL = process.env.EMAIL;
const PASSWORD = process.env.PASSWORD;
if (!EMAIL || !PASSWORD) { console.error('Set EMAIL and PASSWORD env vars'); process.exit(1); }

let token = '';
let clubId = '';
const h = () => ({ 'Content-Type': 'application/json', Authorization: `Bearer ${token}` });

async function j(method, url, body) {
  const res = await fetch(url, { method, headers: h(), body: body != null ? JSON.stringify(body) : undefined });
  const text = await res.text();
  let data; try { data = JSON.parse(text); } catch { data = text; }
  if (!res.ok) throw new Error(`${method} ${url} -> ${res.status} ${text}`);
  return data;
}

async function login() {
  const r = await (await fetch(`${API}/v1/auth/login`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email: EMAIL, password: PASSWORD }) })).json();
  token = r.access_token;
  const me = await j('GET', `${API}/v1/auth/me`);
  clubId = me.clubs[0].club_id;
  const sel = await j('POST', `${API}/v1/auth/select-club`, { club_id: clubId });
  token = sel.access_token;
  console.log('Logged in, club:', me.clubs[0].club_name, clubId);
}

const club = (p) => `${API}/v1/clubs/${clubId}${p}`;

// ── Roster: realistic Polish squad, #1 is the goalkeeper ──
const SQUAD = [
  { number: 1, name: 'Jakub Kowalczyk', gk: true },
  { number: 2, name: 'Michał Nowak' },
  { number: 3, name: 'Tomasz Wiśniewski' },
  { number: 4, name: 'Adam Lewandowski' },
  { number: 5, name: 'Piotr Mazur' },
  { number: 6, name: 'Krzysztof Zieliński' },
  { number: 7, name: 'Marcin Szymański' },
  { number: 8, name: 'Paweł Woźniak' },
  { number: 9, name: 'Bartosz Kamiński' },
  { number: 10, name: 'Łukasz Kaczmarek' },
  { number: 11, name: 'Filip Wójcik' },
  { number: 13, name: 'Jan Dąbrowski' },
];

// Event spec: [jerseyNumber, flagField, quarter]
// Goals per quarter sum to the score deltas: Q1 3, Q2 3, Q3 2, Q4 4 (=12).
const EVENTS = [
  // ── Goals ──
  [9, 'is_goal_from_center_positional', 1], [7, 'is_goal_from_play_positional', 1], [4, 'is_goal_from_play_counter', 1],
  [9, 'is_goal_from_play_counter', 2], [7, 'is_goal_from_play_positional', 2], [5, 'is_goal_from_play_positional', 2],
  [9, 'is_goal_from_center_positional', 3], [11, 'is_goal_from_play_counter', 3],
  [9, 'is_goal_5m_penalty', 4], [7, 'is_goal_from_play_man_up', 4], [4, 'is_goal_from_play_positional', 4], [10, 'is_goal_from_center_man_up', 4],
  // ── Assists ──
  [3, 'is_assist_positional', 1], [6, 'is_assist_positional', 1], [3, 'is_assist_positional', 2],
  [7, 'is_assist_positional', 2], [6, 'is_assist_positional', 3], [4, 'is_assist_positional', 4],
  [3, 'is_assist_man_up', 4], [7, 'is_assist_positional', 4],
  // ── Goalkeeper saves (#1) ──
  [1, 'is_shot_saved_gk_def_positional', 1], [1, 'is_shot_saved_gk_def_positional', 1], [1, 'is_shot_saved_gk_def_positional', 2],
  [1, 'is_shot_saved_gk_def_positional', 2], [1, 'is_shot_saved_gk_def_man_up', 2], [1, 'is_shot_saved_gk_def_positional', 3],
  [1, 'is_shot_saved_gk_def_positional', 3], [1, 'is_shot_saved_gk_def_positional', 4], [1, 'is_shot_saved_gk_def_positional', 4],
  // ── Our shots saved by opp GK ──
  [9, 'is_shot_saved_gk_positional', 1], [7, 'is_shot_saved_gk_positional', 3], [9, 'is_shot_saved_gk_positional', 4],
  // ── Misses / turnovers ──
  [5, 'is_shot_miss_turnover_positional', 2], [8, 'is_shot_miss_turnover_positional', 3],
  [6, 'is_bad_pass_turnover_positional', 1], [10, 'is_bad_pass_turnover_positional', 4], [2, 'is_turnover_1v1_positional', 2],
  // ── Exclusions / penalties drawn ──
  [9, 'is_excl_drawn_center_positional', 1], [9, 'is_excl_drawn_center_positional', 3], [4, 'is_excl_drawn_field_positional', 2],
  [8, 'is_excl_drawn_field_positional', 4], [9, 'is_penalty_drawn_field_positional', 4],
  // ── Steals / blocks (defence) ──
  [2, 'is_steal_positional', 1], [6, 'is_steal_positional', 2], [2, 'is_steal_positional', 3],
  [6, 'is_steal_positional', 4], [3, 'is_steal_positional', 4], [4, 'is_block_hand_positional', 2], [8, 'is_block_hand_positional', 3],
];

const SCORES = [ // quarter -> [my, opp]  CUMULATIVE running totals; the app shows
  // per-quarter deltas by subtracting consecutive quarters (so 3:2, 3:3, 2:1, 4:2).
  ['1', 3, 2], ['2', 6, 5], ['3', 8, 6], ['4', 12, 8], ['final', 12, 8],
];

async function main() {
  await login();

  // 1) Players
  const byNumber = {};
  const playerIds = [];
  for (const p of SQUAD) {
    const created = await j('POST', club('/players'), { number: p.number, name: p.name, birth_year: 2009 });
    const id = created.player_id || created.id;
    byNumber[p.number] = { id, name: p.name };
    playerIds.push(id);
    try { await j('PUT', club(`/players/${id}/age-categories`), { categories: ['U17'] }); } catch {}
  }
  console.log('Created players:', playerIds.length);

  // 2) Match + roster
  const matchId = `match_${Date.now()}`;
  const roster = SQUAD.map(p => ({ player_id: byNumber[p.number].id, number: p.number, name: p.name, team: 'my' }));
  await j('POST', club('/matches'), {
    match: { match_id: matchId, date: '2026-06-14', opponent: 'Arkonia Szczecin', place: 'Pływalnia Bytom', age_category: 'U17' },
    roster,
  });
  await j('PUT', club('/settings/active-match'), { match_id: matchId });
  console.log('Created match:', matchId);

  // 3) Events per quarter (backend tags them with the active match + current quarter)
  for (const q of [1, 2, 3, 4]) {
    await j('PUT', club('/settings/quarter'), { quarter: q });
    const batch = EVENTS.filter(e => e[2] === q).map(([num, flag]) => ({
      player_id: byNumber[num].id, player_name: byNumber[num].name, [flag]: 1,
    }));
    if (batch.length) await j('POST', club('/events'), { events: batch });
    console.log(`Q${q}: ${batch.length} events`);
  }

  // 4) Scores
  for (const [q, my, opp] of SCORES) {
    await j('POST', club(`/matches/${matchId}/scores`), { quarter: q, my_score: my, opp_score: opp });
  }
  console.log('Scores set, final 12:8');

  writeFileSync(new URL('./demo-artifact.json', import.meta.url), JSON.stringify({ clubId, matchId, playerIds }, null, 2));
  console.log('Done. Match left ACTIVE for the live "Asystent" screenshot.');
}

main().catch(e => { console.error('FAILED:', e.message); process.exit(1); });
