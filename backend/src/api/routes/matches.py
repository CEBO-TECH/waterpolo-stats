"""Match routes — port of /api/matches and related endpoints."""

import uuid

from fastapi import APIRouter, HTTPException

from pydantic import BaseModel

from src.api.deps import AnyMember, CoachOrOwner, EventRepo, MatchRepo, RosterRepo, SubstitutionRepo
from src.api.schemas.match import (
    MatchCreate,
    MatchEditRequest,
    MatchResponse,
    MatchWithRosterCreate,
    RosterReplaceRequest,
    ScoreUpdateRequest,
)
from src.domain.models import Match, MatchStatus, RosterEntry, Substitution
from src.domain.services import MvpService, PlaytimeService

router = APIRouter(prefix="/v1/clubs/{club_id}/matches", tags=["matches"])
_playtime_service = PlaytimeService()
_mvp_service = MvpService()


class MvpConfirmRequest(BaseModel):
    player_id: str


@router.get("", response_model=list[MatchResponse])
async def list_matches(
    club_id: str, ctx: AnyMember, repo: MatchRepo, roster_repo: RosterRepo,
):
    matches = await repo.list_active(club_id)
    counts = await roster_repo.get_counts_for_club(club_id)
    return [
        MatchResponse(
            match_id=m.match_id, date=m.date, opponent=m.opponent,
            place=m.place, age_category=m.age_category, status=m.status.value,
            roster_count=counts.get(m.match_id, 0),
        )
        for m in matches
    ]


@router.post("", status_code=201)
async def create_match(
    club_id: str, body: MatchWithRosterCreate,
    ctx: CoachOrOwner, match_repo: MatchRepo, roster_repo: RosterRepo,
):
    match_id = body.match.match_id or f"match_{int(uuid.uuid4().time_low)}"
    match = Match(
        id=str(uuid.uuid4()),
        club_id=club_id,
        match_id=match_id,
        date=body.match.date,
        opponent=body.match.opponent,
        place=body.match.place,
        age_category=body.match.age_category,
    )
    created = await match_repo.upsert(match)

    # Replace roster
    roster_entries = [
        RosterEntry(
            id=str(uuid.uuid4()),
            club_id=club_id,
            match_id=match_id,
            player_id=r.get("player_id", ""),
            number=r.get("number", 0),
            name=r.get("name", ""),
            team=r.get("team", "my"),
        )
        for r in body.roster
    ]
    roster = await roster_repo.replace_for_match(club_id, match_id, roster_entries)

    return {
        "matchId": created.match_id,
        "matches": [
            {
                "match_id": created.match_id, "date": created.date,
                "opponent": created.opponent, "place": created.place,
                "ageCategory": created.age_category, "status": created.status.value,
            }
        ],
        "roster": [
            {"match_id": r.match_id, "player_id": r.player_id, "number": r.number, "name": r.name, "team": r.team}
            for r in roster
        ],
    }


@router.put("/{match_id}", response_model=MatchResponse)
async def edit_match(
    club_id: str, match_id: str, body: MatchEditRequest, ctx: CoachOrOwner, repo: MatchRepo,
):
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    updated = await repo.update_fields(club_id, match_id, fields)
    if not updated:
        raise HTTPException(status_code=404, detail="Match not found")
    return MatchResponse(
        match_id=updated.match_id, date=updated.date, opponent=updated.opponent,
        place=updated.place, age_category=updated.age_category, status=updated.status.value,
    )


@router.post("/{match_id}/end")
async def end_match(
    club_id: str, match_id: str, ctx: CoachOrOwner,
    repo: MatchRepo, sub_repo: SubstitutionRepo,
):
    # Close any open water stints so play-time stops counting at match end.
    subs = await sub_repo.list_for_match(club_id, match_id)
    on_water = _playtime_service.on_water_players(subs)
    if on_water:
        await sub_repo.create_many([
            Substitution(
                id=str(uuid.uuid4()), club_id=club_id, match_id=match_id,
                player_id=pid, direction="out",
            )
            for pid in on_water
        ])

    updated = await repo.update_status(club_id, match_id, MatchStatus.ENDED)
    return {"matchId": updated.match_id, "status": updated.status.value}


@router.post("/{match_id}/archive")
async def archive_match(
    club_id: str, match_id: str, ctx: CoachOrOwner, repo: MatchRepo,
):
    await repo.archive(club_id, match_id)
    return {"matchId": match_id, "archived": True}


@router.get("/{match_id}/roster")
async def get_roster(
    club_id: str, match_id: str, ctx: AnyMember, repo: RosterRepo,
):
    roster = await repo.get_for_match(club_id, match_id)
    return [
        {"match_id": r.match_id, "player_id": r.player_id, "number": r.number, "name": r.name, "team": r.team}
        for r in roster
    ]


@router.put("/{match_id}/roster")
async def set_roster(
    club_id: str, match_id: str, body: RosterReplaceRequest,
    ctx: CoachOrOwner, match_repo: MatchRepo, roster_repo: RosterRepo,
):
    """Replace the roster of an existing match (add squad later / edit squad)."""
    match = await match_repo.get_by_match_id(club_id, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    entries = [
        RosterEntry(
            id=str(uuid.uuid4()),
            club_id=club_id,
            match_id=match_id,
            player_id=r.get("player_id", ""),
            number=r.get("number", 0),
            name=r.get("name", ""),
            team=r.get("team", "my"),
        )
        for r in body.roster
    ]
    roster = await roster_repo.replace_for_match(club_id, match_id, entries)
    return [
        {"match_id": r.match_id, "player_id": r.player_id, "number": r.number, "name": r.name, "team": r.team}
        for r in roster
    ]


@router.get("/{match_id}/previous-roster")
async def get_previous_roster(
    club_id: str, match_id: str, ctx: CoachOrOwner, repo: RosterRepo,
):
    roster = await repo.get_previous_match_roster(club_id, match_id)
    return [
        {"player_id": r.player_id, "number": r.number, "name": r.name, "team": r.team}
        for r in roster
    ]


@router.post("/{match_id}/scores")
async def update_scores(
    club_id: str, match_id: str, body: ScoreUpdateRequest,
    ctx: CoachOrOwner, repo: MatchRepo,
):
    """Port of POST /api/stats/score — save quarter scores."""
    score_fields: dict = {}
    if body.quarter == "final":
        score_fields["final_my"] = body.my_score
        score_fields["final_opp"] = body.opp_score
    elif body.quarter in ("1", "2", "3", "4"):
        score_fields[f"q{body.quarter}_my"] = body.my_score
        score_fields[f"q{body.quarter}_opp"] = body.opp_score
    else:
        raise HTTPException(status_code=400, detail="Invalid quarter")

    updated = await repo.update_scores(club_id, match_id, score_fields)
    return updated.per_quarter_scores()


def _mvp_dto(e) -> dict:
    return {
        "player_id": e.player_id, "player_name": e.player_name, "score": e.score,
        "goals": e.goals, "assists": e.assists, "steals": e.steals,
        "blocks": e.blocks, "turnovers": e.turnovers, "fouls": e.fouls,
    }


@router.get("/{match_id}/mvp")
async def get_mvp(
    club_id: str, match_id: str, ctx: AnyMember,
    match_repo: MatchRepo, event_repo: EventRepo, roster_repo: RosterRepo,
):
    """Suggested MVP (ranking by weighted contribution) + confirmed pick if any."""
    match = await match_repo.get_by_match_id(club_id, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    events = await event_repo.get_all_for_match(club_id, match_id)
    roster = await roster_repo.get_for_match(club_id, match_id)
    ranking = _mvp_service.compute(events, roster)
    return {
        "suggested": _mvp_dto(ranking[0]) if ranking else None,
        "ranking": [_mvp_dto(e) for e in ranking[:5]],
        "confirmed_player_id": match.mvp_player_id,
    }


@router.put("/{match_id}/mvp")
async def confirm_mvp(
    club_id: str, match_id: str, body: MvpConfirmRequest,
    ctx: CoachOrOwner, repo: MatchRepo,
):
    """Coach confirms / overrides the MVP for a match."""
    updated = await repo.update_fields(club_id, match_id, {"mvp_player_id": body.player_id})
    if not updated:
        raise HTTPException(status_code=404, detail="Match not found")
    return {"matchId": updated.match_id, "mvp_player_id": updated.mvp_player_id}
