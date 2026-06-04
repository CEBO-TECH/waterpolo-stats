"""Match routes — port of /api/matches and related endpoints."""

import uuid

from fastapi import APIRouter, HTTPException

from src.api.deps import AnyMember, CoachOrOwner, MatchRepo, RosterRepo
from src.api.schemas.match import (
    MatchCreate,
    MatchEditRequest,
    MatchResponse,
    MatchWithRosterCreate,
    ScoreUpdateRequest,
)
from src.domain.models import Match, MatchStatus, RosterEntry

router = APIRouter(prefix="/v1/clubs/{club_id}/matches", tags=["matches"])


@router.get("", response_model=list[MatchResponse])
async def list_matches(
    club_id: str, ctx: AnyMember, repo: MatchRepo,
):
    matches = await repo.list_active(club_id)
    return [
        MatchResponse(
            match_id=m.match_id, date=m.date, opponent=m.opponent,
            place=m.place, age_category=m.age_category, status=m.status.value,
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
    club_id: str, match_id: str, ctx: CoachOrOwner, repo: MatchRepo,
):
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
