"""Convert between SQLAlchemy ORM models and domain dataclasses."""

from src.domain.models import (
    Club,
    ClubConfig,
    ClubMembership,
    ClubSettings,
    ClubType,
    Event,
    EVENT_FLAG_FIELDS,
    Match,
    MatchStatus,
    Player,
    PlayerAgeCategory,
    RosterEntry,
    Season,
    User,
    UserRole,
    YouTubeStream,
)
from src.domain.models.config import AVAILABLE_MODULES

from . import models as orm


def club_to_domain(m: orm.ClubModel) -> Club:
    return Club(
        id=m.id, name=m.name,
        club_type=ClubType(m.club_type),
        created_at=m.created_at, updated_at=m.updated_at,
    )


def user_to_domain(m: orm.UserModel) -> User:
    return User(
        id=m.id, email=m.email, hashed_password=m.hashed_password,
        created_at=m.created_at, updated_at=m.updated_at,
    )


def membership_to_domain(m: orm.ClubMembershipModel) -> ClubMembership:
    return ClubMembership(
        id=m.id, user_id=m.user_id, club_id=m.club_id,
        role=UserRole(m.role), created_at=m.created_at,
    )


def settings_to_domain(m: orm.ClubSettingsModel) -> ClubSettings:
    return ClubSettings(
        id=m.id, club_id=m.club_id,
        active_match=m.active_match or "",
        quarter=m.quarter or 1,
        editor_pin=m.editor_pin or "",
        created_at=m.created_at, updated_at=m.updated_at,
    )


def player_to_domain(m: orm.PlayerModel) -> Player:
    return Player(
        id=m.id, club_id=m.club_id, player_id=m.player_id,
        number=m.number, name=m.name, team=m.team,
        created_at=m.created_at, updated_at=m.updated_at,
    )


def player_age_cat_to_domain(m: orm.PlayerAgeCategoryModel) -> PlayerAgeCategory:
    return PlayerAgeCategory(id=m.id, player_id=m.player_id, age_category=m.age_category)


def season_to_domain(m: orm.SeasonModel) -> Season:
    return Season(
        id=m.id, club_id=m.club_id, name=m.name,
        start_date=m.start_date, end_date=m.end_date,
        is_active=m.is_active,
        created_at=m.created_at, updated_at=m.updated_at,
    )


def match_to_domain(m: orm.MatchModel) -> Match:
    return Match(
        id=m.id, club_id=m.club_id, match_id=m.match_id,
        date=m.date, opponent=m.opponent, place=m.place,
        age_category=m.age_category,
        status=MatchStatus(m.status), archived=m.archived,
        season_id=m.season_id,
        q1_my=m.q1_my, q1_opp=m.q1_opp,
        q2_my=m.q2_my, q2_opp=m.q2_opp,
        q3_my=m.q3_my, q3_opp=m.q3_opp,
        q4_my=m.q4_my, q4_opp=m.q4_opp,
        final_my=m.final_my, final_opp=m.final_opp,
        created_at=m.created_at, updated_at=m.updated_at,
    )


def roster_to_domain(m: orm.MatchRosterModel) -> RosterEntry:
    return RosterEntry(
        id=m.id, club_id=m.club_id, match_id=m.match_id,
        player_id=m.player_id, number=m.number,
        name=m.name, team=m.team, created_at=m.created_at,
    )


def event_to_domain(m: orm.EventModel) -> Event:
    kwargs = {
        "id": m.id, "club_id": m.club_id, "match_id": m.match_id,
        "player_id": m.player_id, "player_name": m.player_name,
        "quarter": m.quarter, "team": m.team,
        "event_type": m.event_type or "", "subtype": m.subtype or "",
        "value": m.value or "", "note": m.note or "",
        "video_timestamp": m.video_timestamp,
        "timestamp": m.timestamp,
    }
    for flag in EVENT_FLAG_FIELDS:
        kwargs[flag] = getattr(m, flag, 0) or 0
    return Event(**kwargs)


def youtube_to_domain(m: orm.YouTubeStreamModel) -> YouTubeStream:
    return YouTubeStream(
        id=m.id, match_id=m.match_id,
        youtube_url=m.youtube_url, video_id=m.video_id,
        stream_start_time=m.stream_start_time,
        created_at=m.created_at,
    )


def config_to_domain(m: orm.ClubConfigModel) -> ClubConfig:
    modules = m.active_modules if isinstance(m.active_modules, list) else list(AVAILABLE_MODULES)
    return ClubConfig(
        id=m.id, club_id=m.club_id,
        active_modules=modules,
        button_layout=m.button_layout or {},
        updated_at=m.updated_at,
    )
