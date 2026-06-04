/**
 * API base URL:
 * - Production: set via NEXT_PUBLIC_API_URL env var (e.g. https://api.wts-stats.cebo.tech)
 * - Dev: http://localhost:8000
 */
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('access_token');
  }

  private getClubId(): string {
    if (typeof window === 'undefined') return '';
    return localStorage.getItem('club_id') || '';
  }

  private headers(extra?: Record<string, string>): Record<string, string> {
    const h: Record<string, string> = {
      'Content-Type': 'application/json',
      'Cache-Control': 'no-cache',
      ...extra,
    };
    const token = this.getToken();
    if (token) h['Authorization'] = `Bearer ${token}`;
    return h;
  }

  private clubUrl(path: string): string {
    return `${API_URL}/v1/clubs/${this.getClubId()}${path}`;
  }

  async fetch(url: string, options?: RequestInit): Promise<Response> {
    const res = await fetch(url, {
      ...options,
      cache: 'no-store',
      headers: this.headers(options?.headers as Record<string, string>),
    });
    return res;
  }

  // ─── Auth ───

  async register(email: string, password: string) {
    const res = await fetch(`${API_URL}/v1/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    return res.json();
  }

  async login(email: string, password: string) {
    const res = await fetch(`${API_URL}/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) throw new Error('Invalid credentials');
    const data = await res.json();
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    return data;
  }

  async getMe() {
    const res = await this.fetch(`${API_URL}/v1/auth/me`);
    if (!res.ok) throw new Error('Not authenticated');
    return res.json();
  }

  // ─── Clubs ───

  async createClub(name: string) {
    const res = await this.fetch(`${API_URL}/v1/clubs`, {
      method: 'POST',
      body: JSON.stringify({ name }),
    });
    return res.json();
  }

  // ─── Bootstrap ───

  async bootstrap() {
    const res = await this.fetch(this.clubUrl(`/bootstrap?t=${Date.now()}`));
    if (!res.ok) throw new Error('Bootstrap failed');
    return res.json();
  }

  // ─── Settings ───

  async setActiveMatch(matchId: string) {
    const res = await this.fetch(this.clubUrl('/settings/active-match'), {
      method: 'PUT',
      body: JSON.stringify({ match_id: matchId }),
    });
    return res.json();
  }

  async setQuarter(quarter: number) {
    const res = await this.fetch(this.clubUrl('/settings/quarter'), {
      method: 'PUT',
      body: JSON.stringify({ quarter }),
    });
    return res.json();
  }

  // ─── Players ───

  async getPlayers() {
    const res = await this.fetch(this.clubUrl('/players'));
    return res.json();
  }

  async createPlayer(number: number, name: string) {
    const res = await this.fetch(this.clubUrl('/players'), {
      method: 'POST',
      body: JSON.stringify({ number, name }),
    });
    return res.json();
  }

  async deletePlayer(playerId: string) {
    const res = await this.fetch(this.clubUrl(`/players/${playerId}`), {
      method: 'DELETE',
    });
    return res.json();
  }

  // ─── Matches ───

  async getMatches() {
    const res = await this.fetch(this.clubUrl('/matches'));
    return res.json();
  }

  async createMatch(match: any, roster: any[]) {
    const res = await this.fetch(this.clubUrl('/matches'), {
      method: 'POST',
      body: JSON.stringify({ match, roster }),
    });
    return res.json();
  }

  async editMatch(matchId: string, fields: any) {
    const res = await this.fetch(this.clubUrl(`/matches/${matchId}`), {
      method: 'PUT',
      body: JSON.stringify(fields),
    });
    return res.json();
  }

  async endMatch(matchId: string) {
    const res = await this.fetch(this.clubUrl(`/matches/${matchId}/end`), {
      method: 'POST',
    });
    return res.json();
  }

  async archiveMatch(matchId: string) {
    const res = await this.fetch(this.clubUrl(`/matches/${matchId}/archive`), {
      method: 'POST',
    });
    return res.json();
  }

  async getRoster(matchId: string) {
    const res = await this.fetch(this.clubUrl(`/matches/${matchId}/roster`));
    return res.json();
  }

  async getPreviousRoster(matchId: string) {
    const res = await this.fetch(this.clubUrl(`/matches/${matchId}/previous-roster`));
    return res.json();
  }

  async updateScore(matchId: string, quarter: string, myScore: number, oppScore: number) {
    const res = await this.fetch(this.clubUrl(`/matches/${matchId}/scores`), {
      method: 'POST',
      body: JSON.stringify({ quarter, my_score: myScore, opp_score: oppScore }),
    });
    return res.json();
  }

  // ─── Events ───

  async createEvents(events: any[]) {
    const res = await this.fetch(this.clubUrl('/events'), {
      method: 'POST',
      body: JSON.stringify({ events }),
    });
    return res.json();
  }

  async getEvents(matchId: string, limit = 20) {
    const res = await this.fetch(this.clubUrl(`/matches/${matchId}/events?limit=${limit}`));
    return res.json();
  }

  async deleteEvent(eventId: string) {
    const res = await this.fetch(this.clubUrl(`/events/${eventId}`), {
      method: 'DELETE',
    });
    return res.json();
  }

  async undoEvent(windowMinutes = 3) {
    const res = await this.fetch(this.clubUrl('/events/undo'), {
      method: 'POST',
      body: JSON.stringify({ window_minutes: windowMinutes }),
    });
    return res.json();
  }

  // ─── Stats ───

  async getMatchStats(matchId: string) {
    const res = await this.fetch(this.clubUrl(`/matches/${matchId}/stats?t=${Date.now()}`));
    return res.json();
  }

  async getPlayerProfile(playerId: string, seasonId?: string) {
    let url = this.clubUrl(`/players/${playerId}/stats`);
    if (seasonId) url += `?season_id=${seasonId}`;
    const res = await this.fetch(url);
    return res.json();
  }

  // ─── YouTube ───

  async attachYouTube(matchId: string, youtubeUrl: string, streamStartTime?: string) {
    const res = await this.fetch(this.clubUrl(`/matches/${matchId}/youtube`), {
      method: 'POST',
      body: JSON.stringify({ youtube_url: youtubeUrl, stream_start_time: streamStartTime }),
    });
    return res.json();
  }

  async getYouTube(matchId: string) {
    const res = await this.fetch(this.clubUrl(`/matches/${matchId}/youtube`));
    if (!res.ok) return null;
    return res.json();
  }

  // ─── Config ───

  async getConfig() {
    const res = await this.fetch(this.clubUrl('/config'));
    return res.json();
  }

  async updateConfig(activeModules: string[], buttonLayout: any = {}) {
    const res = await this.fetch(this.clubUrl('/config'), {
      method: 'PUT',
      body: JSON.stringify({ active_modules: activeModules, button_layout: buttonLayout }),
    });
    return res.json();
  }

  // ─── Utils ───

  setClubId(clubId: string) {
    localStorage.setItem('club_id', clubId);
  }

  logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('club_id');
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }
}

export const api = new ApiClient();
