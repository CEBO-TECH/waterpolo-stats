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

  /** Re-issue an access token scoped to the chosen club and make it active. */
  async selectClub(clubId: string) {
    const res = await this.fetch(`${API_URL}/v1/auth/select-club`, {
      method: 'POST',
      body: JSON.stringify({ club_id: clubId }),
    });
    if (!res.ok) throw new Error('Nie udało się wybrać klubu');
    const data = await res.json();
    localStorage.setItem('access_token', data.access_token);
    if (data.refresh_token) localStorage.setItem('refresh_token', data.refresh_token);
    this.setClubId(clubId);
    return data;
  }

  // ─── Clubs ───

  async createClub(name: string) {
    const res = await this.fetch(`${API_URL}/v1/clubs`, {
      method: 'POST',
      body: JSON.stringify({ name }),
    });
    return res.json();
  }

  // ─── Members / invitations ───

  async getMembers() {
    const res = await this.fetch(this.clubUrl('/members'));
    if (!res.ok) throw new Error('Brak dostępu do listy użytkowników');
    return res.json();
  }

  async inviteMember(email: string, role: string) {
    const res = await this.fetch(this.clubUrl('/invite'), {
      method: 'POST',
      body: JSON.stringify({ email, role }),
    });
    if (!res.ok) {
      const e = await res.json().catch(() => ({}));
      throw new Error(e.detail || 'Nie udało się zaprosić');
    }
    return res.json();
  }

  async updateMemberRole(userId: string, role: string) {
    const res = await this.fetch(this.clubUrl(`/members/${userId}`), {
      method: 'PATCH',
      body: JSON.stringify({ role }),
    });
    if (!res.ok) {
      const e = await res.json().catch(() => ({}));
      throw new Error(e.detail || 'Nie udało się zmienić roli');
    }
    return res.json();
  }

  async removeMember(userId: string) {
    const res = await this.fetch(this.clubUrl(`/members/${userId}`), { method: 'DELETE' });
    if (!res.ok) {
      const e = await res.json().catch(() => ({}));
      throw new Error(e.detail || 'Nie udało się usunąć');
    }
    return res.json();
  }

  async getInvitations() {
    const res = await this.fetch(this.clubUrl('/invitations'));
    if (!res.ok) return [];
    return res.json();
  }

  async revokeInvitation(invitationId: string) {
    const res = await this.fetch(this.clubUrl(`/invitations/${invitationId}`), { method: 'DELETE' });
    return res.json();
  }

  async acceptInvitation(token: string) {
    const res = await this.fetch(`${API_URL}/v1/invitations/${token}/accept`, { method: 'POST' });
    if (!res.ok) throw new Error('Nie udało się przyjąć zaproszenia');
    return res.json();
  }

  // ─── Dashboard ───

  async getDashboard(ageCategory?: string) {
    const params: string[] = [`t=${Date.now()}`];
    if (ageCategory) params.push(`age_category=${encodeURIComponent(ageCategory)}`);
    const res = await this.fetch(this.clubUrl(`/dashboard?${params.join('&')}`));
    if (!res.ok) throw new Error('Nie udało się pobrać dashboardu');
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

  async createPlayer(
    number: number, name: string,
    extra: { birth_year?: number | null; email?: string | null } = {},
  ) {
    const res = await this.fetch(this.clubUrl('/players'), {
      method: 'POST',
      body: JSON.stringify({ number, name, ...extra }),
    });
    return res.json();
  }

  async updatePlayer(playerId: string, fields: { number?: number; name?: string; team?: string; birth_year?: number | null; email?: string | null }) {
    const res = await this.fetch(this.clubUrl(`/players/${playerId}`), {
      method: 'PUT',
      body: JSON.stringify(fields),
    });
    if (!res.ok) throw new Error('Nie udało się zapisać zawodnika');
    return res.json();
  }

  async deletePlayer(playerId: string) {
    const res = await this.fetch(this.clubUrl(`/players/${playerId}`), {
      method: 'DELETE',
    });
    return res.json();
  }

  async setPlayerAgeCategories(playerId: string, categories: string[]) {
    const res = await this.fetch(this.clubUrl(`/players/${playerId}/age-categories`), {
      method: 'PUT',
      body: JSON.stringify({ categories }),
    });
    if (!res.ok) throw new Error('Nie udało się zapisać kategorii');
    return res.json();
  }

  // ─── Age categories (club dictionary) ───

  async getAgeCategories() {
    const res = await this.fetch(this.clubUrl('/age-categories'));
    return res.json();
  }

  async createAgeCategory(name: string) {
    const res = await this.fetch(this.clubUrl('/age-categories'), {
      method: 'POST',
      body: JSON.stringify({ name }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Nie udało się dodać kategorii');
    }
    return res.json();
  }

  async deleteAgeCategory(categoryId: string) {
    const res = await this.fetch(this.clubUrl(`/age-categories/${categoryId}`), {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Nie udało się usunąć kategorii');
    return res.json();
  }

  // ─── Matches ───

  async getMatches() {
    const res = await this.fetch(this.clubUrl('/matches'));
    return res.json();
  }

  async createMatch(match: any, roster: any[]) {
    // Backend expects snake_case `age_category`; UI carries `ageCategory`.
    const payload = {
      match: {
        match_id: match.match_id,
        date: match.date || '',
        opponent: match.opponent || '',
        place: match.place || '',
        age_category: match.ageCategory ?? match.age_category ?? '',
      },
      roster,
    };
    const res = await this.fetch(this.clubUrl('/matches'), {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return res.json();
  }

  async editMatch(matchId: string, fields: any) {
    const body: any = { ...fields };
    if ('ageCategory' in body) {
      body.age_category = body.ageCategory;
      delete body.ageCategory;
    }
    const res = await this.fetch(this.clubUrl(`/matches/${matchId}`), {
      method: 'PUT',
      body: JSON.stringify(body),
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

  async setRoster(matchId: string, roster: any[]) {
    const res = await this.fetch(this.clubUrl(`/matches/${matchId}/roster`), {
      method: 'PUT',
      body: JSON.stringify({ roster }),
    });
    if (!res.ok) throw new Error('Nie udało się zapisać składu');
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

  // ─── Substitutions / play-time ───

  async getPlaytime(matchId: string) {
    const res = await this.fetch(this.clubUrl(`/matches/${matchId}/playtime?t=${Date.now()}`));
    if (!res.ok) return { players: {} };
    return res.json();
  }

  async recordSubstitution(matchId: string, playerId: string, direction: 'in' | 'out', quarter = 1) {
    const res = await this.fetch(this.clubUrl(`/matches/${matchId}/substitutions`), {
      method: 'POST',
      body: JSON.stringify({ player_id: playerId, direction, quarter }),
    });
    if (!res.ok) throw new Error('Nie udało się zapisać zmiany');
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

  // ─── Voice notes ───

  async uploadVoiceNote(
    matchId: string, blob: Blob,
    opts: { duration_s?: number; note?: string; player_id?: string } = {},
  ) {
    const fd = new FormData();
    fd.append('file', blob, 'note.webm');
    if (opts.duration_s != null) fd.append('duration_s', String(opts.duration_s));
    if (opts.note) fd.append('note', opts.note);
    if (opts.player_id) fd.append('player_id', opts.player_id);
    const token = this.getToken();
    const res = await fetch(this.clubUrl(`/matches/${matchId}/voice-notes`), {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: fd,
    });
    if (!res.ok) throw new Error('Nie udało się wysłać notatki');
    return res.json();
  }

  async getVoiceNotes(matchId: string) {
    const res = await this.fetch(this.clubUrl(`/matches/${matchId}/voice-notes`));
    if (!res.ok) return [];
    return res.json();
  }

  async getVoiceNoteAudioUrl(matchId: string, noteId: string): Promise<string | null> {
    const res = await this.fetch(this.clubUrl(`/matches/${matchId}/voice-notes/${noteId}/audio`));
    if (!res.ok) return null;
    const blob = await res.blob();
    return URL.createObjectURL(blob);
  }

  async deleteVoiceNote(matchId: string, noteId: string) {
    const res = await this.fetch(this.clubUrl(`/matches/${matchId}/voice-notes/${noteId}`), { method: 'DELETE' });
    return res.json();
  }

  // ─── Player self-service ───

  async getMyPlayer() {
    const res = await this.fetch(this.clubUrl('/me/player'));
    if (!res.ok) return { player: null };
    return res.json();
  }

  async getMyMatches() {
    const res = await this.fetch(this.clubUrl('/me/matches'));
    if (!res.ok) return [];
    return res.json();
  }

  async getMvp(matchId: string) {
    const res = await this.fetch(this.clubUrl(`/matches/${matchId}/mvp?t=${Date.now()}`));
    if (!res.ok) return null;
    return res.json();
  }

  async confirmMvp(matchId: string, playerId: string) {
    const res = await this.fetch(this.clubUrl(`/matches/${matchId}/mvp`), {
      method: 'PUT',
      body: JSON.stringify({ player_id: playerId }),
    });
    if (!res.ok) throw new Error('Nie udało się zapisać MVP');
    return res.json();
  }

  async getMultiStats(matchIds: string[]) {
    const res = await this.fetch(this.clubUrl('/stats/multi'), {
      method: 'POST',
      body: JSON.stringify({ match_ids: matchIds }),
    });
    if (!res.ok) throw new Error('Nie udało się pobrać statystyk');
    return res.json();
  }

  async getPlayerProfile(playerId: string, seasonId?: string) {
    let url = this.clubUrl(`/players/${playerId}/stats`);
    if (seasonId) url += `?season_id=${seasonId}`;
    const res = await this.fetch(url);
    return res.json();
  }

  // ─── YouTube ───

  async attachYouTube(
    matchId: string,
    youtubeUrl: string,
    opts: { streamStartTime?: string; startNow?: boolean } = {},
  ) {
    const res = await this.fetch(this.clubUrl(`/matches/${matchId}/youtube`), {
      method: 'POST',
      body: JSON.stringify({
        youtube_url: youtubeUrl,
        stream_start_time: opts.streamStartTime,
        start_now: opts.startNow || false,
      }),
    });
    if (!res.ok) {
      const e = await res.json().catch(() => ({}));
      throw new Error(e.detail || 'Nie udało się zapisać streamu');
    }
    return res.json();
  }

  async getYouTube(matchId: string) {
    const res = await this.fetch(this.clubUrl(`/matches/${matchId}/youtube`));
    if (!res.ok) return null;
    return res.json();
  }

  async getEventVideoUrl(matchId: string, eventId: string) {
    const res = await this.fetch(this.clubUrl(`/matches/${matchId}/events/${eventId}/video-url`));
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

  getCurrentClubId(): string {
    return this.getClubId();
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
