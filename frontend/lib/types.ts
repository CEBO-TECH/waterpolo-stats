export type Player = {
  player_id: string;
  number: number;
  name: string;
  team: string;
  age_categories?: string[];
  birth_year?: number | null;
  email?: string | null;
  has_account?: boolean;
};

export type AgeCategory = {
  id: string;
  name: string;
  sort_order?: number;
};

// Fallback used only when a club has no categories yet (np. starsze kluby przed migracją).
export const AGE_CATEGORIES = ['Seniorzy', 'U19', 'U17', 'U15'];

export type Match = {
  match_id: string;
  date: string;
  opponent: string;
  place: string;
  ageCategory: string;
  status: string;
  rosterCount?: number;
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

export type ClubInfo = {
  club_id: string;
  club_name: string;
  role: string;
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
  clubs: ClubInfo[];
  currentClubId: string;
  ageCategories: AgeCategory[];
  youtube: YouTubeInfo | null;
};

export type YouTubeInfo = {
  youtube_url: string;
  video_id: string;
  stream_start_time: string | null;
};

export type Mode = 'dashboard' | 'score' | 'stats' | 'admin' | 'players' | 'matches' | 'users';
