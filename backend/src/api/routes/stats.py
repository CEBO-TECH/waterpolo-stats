"""Stats routes — port of GET /api/stats/[matchId] + new player profile & season stats."""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from src.api.deps import AnyMember, EventRepo, MatchRepo, PlayerRepo, RosterRepo, SeasonRepo
from src.domain.services import PlayerProfileService, StatsService, TeamStatsService

router = APIRouter(prefix="/v1/clubs/{club_id}", tags=["stats"])
stats_service = StatsService()
player_profile_service = PlayerProfileService()
team_stats_service = TeamStatsService()


@router.get("/matches/{match_id}/stats")
async def get_match_stats(
    club_id: str, match_id: str,
    ctx: AnyMember,
    event_repo: EventRepo,
    roster_repo: RosterRepo,
    match_repo: MatchRepo,
):
    """Aggregated stats for a match. Port of GET /api/stats/[matchId]."""
    match = await match_repo.get_by_match_id(club_id, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    events = await event_repo.get_all_for_match(club_id, match_id)
    roster = await roster_repo.get_for_match(club_id, match_id)

    result = stats_service.compute_match_stats(events, roster, match)

    return JSONResponse(
        content={
            "flags": result.flags,
            "players": result.players,
            "perPlayerAll": result.per_player_all,
            "perPlayerByQ": result.per_player_by_q,
            "totalsAll": result.totals_all,
            "totalsByQ": result.totals_by_q,
            "scores": result.scores,
        },
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
        },
    )


@router.get("/players/{player_id}/stats")
async def get_player_profile(
    club_id: str, player_id: str,
    ctx: AnyMember,
    player_repo: PlayerRepo,
    event_repo: EventRepo,
    match_repo: MatchRepo,
    season_id: str | None = Query(default=None),
):
    """Player profile with cross-match stats, effectiveness, and trend."""
    player = await player_repo.get_by_player_id(club_id, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    events = await event_repo.get_all_for_player(club_id, player_id, season_id)
    matches = await match_repo.list_active(club_id)

    profile = player_profile_service.compute_player_profile(
        player_id, player.name, events, matches
    )

    return {
        "player_id": profile.player_id,
        "player_name": profile.player_name,
        "total_matches": profile.total_matches,
        "total_goals": profile.total_goals,
        "total_shots": profile.total_shots,
        "overall_effectiveness": profile.overall_effectiveness,
        "total_assists": profile.total_assists,
        "total_turnovers": profile.total_turnovers,
        "total_exclusions": profile.total_exclusions,
        "total_steals": profile.total_steals,
        "total_blocks": profile.total_blocks,
        "flag_totals": profile.flag_totals,
        "match_trend": [
            {
                "match_id": mp.match_id,
                "match_date": mp.match_date,
                "opponent": mp.opponent,
                "goals": mp.goals,
                "shots": mp.shots,
                "shot_effectiveness": mp.shot_effectiveness,
                "assists": mp.assists,
                "turnovers": mp.turnovers,
                "exclusions": mp.exclusions,
                "steals": mp.steals,
                "blocks": mp.blocks,
            }
            for mp in profile.match_trend
        ],
    }


@router.get("/seasons/{season_id}/stats")
async def get_season_stats(
    club_id: str, season_id: str,
    ctx: AnyMember,
    season_repo: SeasonRepo,
    match_repo: MatchRepo,
    event_repo: EventRepo,
    age_category: str | None = Query(default=None),
    opponent: str | None = Query(default=None),
):
    """Season summary with W/L/D, rankings, and filtering."""
    season = await season_repo.get_by_id(club_id, season_id)
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")

    matches = await match_repo.list_by_season(club_id, season_id)
    events = await event_repo.get_all_for_season(club_id, season_id)

    summary = team_stats_service.compute_season_summary(
        season_id, season.name, matches, events,
        age_category=age_category, opponent=opponent,
    )

    return {
        "season_id": summary.season_id,
        "season_name": summary.season_name,
        "total_matches": summary.total_matches,
        "wins": summary.wins,
        "losses": summary.losses,
        "draws": summary.draws,
        "goals_for": summary.goals_for,
        "goals_against": summary.goals_against,
        "goal_difference": summary.goal_difference,
        "top_scorers": [
            {"player_id": r.player_id, "player_name": r.player_name, "value": r.value}
            for r in summary.top_scorers
        ],
        "top_assistants": [
            {"player_id": r.player_id, "player_name": r.player_name, "value": r.value}
            for r in summary.top_assistants
        ],
        "top_stealers": [
            {"player_id": r.player_id, "player_name": r.player_name, "value": r.value}
            for r in summary.top_stealers
        ],
    }
