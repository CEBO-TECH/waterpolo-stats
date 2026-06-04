export type Player = {
  player_id: string;
  number: number;
  name: string;
  team: string;
};

export type Match = {
  match_id: string;
  date: string;
  opponent: string;
  place: string;
  ageCategory: string;
  status: string;
};

export type Settings = {
  ActiveMatch: string;
  Quarter: number;
};

export type RecentEvent = {
  id: string;
  timestamp: string;
  quarter: number;
  player_name: string;
  event_type: string;
  note: string;
  action: string;
};

export type AppState = {
  settings: Settings | null;
  players: Player[];
  matches: Match[];
  selected: Player | null;
  stats: any;
  user: { email: string; role: string } | null;
  rosterActive: Player[];
  recentEvents: RecentEvent[];
  config: { active_modules: string[]; button_layout: any } | null;
};

export type Mode = 'score' | 'stats' | 'admin' | 'players' | 'matches';
