"""Player self-service routes — a logged-in PLAYER's own player + matches."""

from fastapi import APIRouter

from src.api.deps import AnyMember, MatchRepo, PlayerRepo, RosterRepo
from src.domain.models import MatchStatus

router = APIRouter(prefix="/v1/clubs/{club_id}/me", tags=["me"])


@router.get("/player")
async def my_player(club_id: str, ctx: AnyMember, repo: PlayerRepo):
    """The Player linked to the logged-in user (or null)."""
    user, _ = ctx
    player = await repo.get_by_user_id(club_id, user.id)
    if not player:
        return {"player": None}
    cats = await repo.get_age_categories(player.player_id)
    return {
        "player": {
            "player_id": player.player_id, "number": player.number, "name": player.name,
            "birth_year": player.birth_year,
            "age_categories": [c.age_category for c in cats],
        }
    }


@router.get("/matches")
async def my_matches(
    club_id: str, ctx: AnyMember,
    player_repo: PlayerRepo, roster_repo: RosterRepo, match_repo: MatchRepo,
):
    """Matches the logged-in player was on the roster for."""
    user, _ = ctx
    player = await player_repo.get_by_user_id(club_id, user.id)
    if not player:
        return []

    match_ids = set(await roster_repo.get_match_ids_for_player(club_id, player.player_id))
    out = []
    for mid in match_ids:
        m = await match_repo.get_by_match_id(club_id, mid)
        if not m:
            continue
        my = m.final_my or m.q4_my
        opp = m.final_opp or m.q4_opp
        result = ""
        if m.status == MatchStatus.ENDED:
            result = "W" if my > opp else "L" if my < opp else "D"
        out.append({
            "match_id": m.match_id, "date": m.date, "opponent": m.opponent,
            "ageCategory": m.age_category, "status": m.status.value,
            "my_score": my, "opp_score": opp, "result": result,
            "is_mvp": m.mvp_player_id == player.player_id,
        })
    out.sort(key=lambda x: x["date"], reverse=True)
    return out
