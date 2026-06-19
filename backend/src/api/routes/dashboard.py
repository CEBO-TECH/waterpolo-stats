"""Dashboard route — aggregated club overview (KPIs, recent matches, rankings)."""

from fastapi import APIRouter, Query

from src.api.deps import AnyMember, EventRepo, MatchRepo, SettingsRepo
from src.domain.services import DashboardService

router = APIRouter(prefix="/v1/clubs/{club_id}", tags=["dashboard"])
dashboard_service = DashboardService()


def _match_dto(m) -> dict:
    return {
        "match_id": m.match_id,
        "date": m.date,
        "opponent": m.opponent,
        "ageCategory": m.age_category,
        "status": m.status,
        "my_score": m.my_score,
        "opp_score": m.opp_score,
        "result": m.result,
    }


@router.get("/dashboard")
async def get_dashboard(
    club_id: str,
    ctx: AnyMember,
    match_repo: MatchRepo,
    event_repo: EventRepo,
    settings_repo: SettingsRepo,
    season_id: str | None = Query(default=None),
    age_category: str | None = Query(default=None),
):
    if season_id:
        matches = await match_repo.list_by_season(club_id, season_id)
        events = await event_repo.get_all_for_season(club_id, season_id)
    else:
        matches = await match_repo.list_active(club_id)
        events = await event_repo.get_all_for_club(club_id)

    settings = await settings_repo.get_for_club(club_id)
    overview = dashboard_service.compute_overview(
        matches, events,
        active_match_id=settings.active_match,
        age_category=age_category,
    )

    return {
        "total_matches": overview.total_matches,
        "wins": overview.wins,
        "losses": overview.losses,
        "draws": overview.draws,
        "goals_for": overview.goals_for,
        "goals_against": overview.goals_against,
        "goal_difference": overview.goal_difference,
        "top_scorers": [
            {"player_id": r.player_id, "player_name": r.player_name, "value": r.value}
            for r in overview.top_scorers
        ],
        "top_assistants": [
            {"player_id": r.player_id, "player_name": r.player_name, "value": r.value}
            for r in overview.top_assistants
        ],
        "recent_matches": [_match_dto(m) for m in overview.recent_matches],
        "active_match": _match_dto(overview.active_match) if overview.active_match else None,
    }
