"""SQLAlchemy ORM table models.

Maps 1:1 from the Prisma schema (@@map names preserved) plus new multi-tenancy tables.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


# ──────────────────────────── NEW: Multi-tenancy ────────────────────────────


class ClubModel(Base):
    __tablename__ = "clubs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    club_type: Mapped[str] = mapped_column(String, default="regular")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    memberships = relationship("ClubMembershipModel", back_populates="club")
    settings = relationship("ClubSettingsModel", back_populates="club", uselist=False)
    config = relationship("ClubConfigModel", back_populates="club", uselist=False)


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    memberships = relationship("ClubMembershipModel", back_populates="user")


class ClubInvitationModel(Base):
    __tablename__ = "club_invitations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    club_id: Mapped[str] = mapped_column(String, ForeignKey("clubs.id"), nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False, default="player")
    token: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ClubMembershipModel(Base):
    __tablename__ = "club_memberships"
    __table_args__ = (UniqueConstraint("user_id", "club_id"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    club_id: Mapped[str] = mapped_column(String, ForeignKey("clubs.id"), nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False, default="player")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user = relationship("UserModel", back_populates="memberships")
    club = relationship("ClubModel", back_populates="memberships")


# ──────────────────────────── NEW: Seasons ────────────────────────────


class SeasonModel(Base):
    __tablename__ = "seasons"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    club_id: Mapped[str] = mapped_column(String, ForeignKey("clubs.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    start_date: Mapped[str] = mapped_column(String, nullable=False)
    end_date: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


# ──────────────────────── EXISTING: Settings (per-club) ──────────────────────


class ClubSettingsModel(Base):
    __tablename__ = "club_settings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    club_id: Mapped[str] = mapped_column(String, ForeignKey("clubs.id"), unique=True, nullable=False)
    active_match: Mapped[str] = mapped_column(String, default="")
    quarter: Mapped[int] = mapped_column(Integer, default=1)
    editor_pin: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    club = relationship("ClubModel", back_populates="settings")


# ──────────────────────── EXISTING: Players ──────────────────────


class PlayerModel(Base):
    __tablename__ = "players"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    club_id: Mapped[str] = mapped_column(String, ForeignKey("clubs.id"), nullable=False)
    player_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    number: Mapped[int] = mapped_column(Integer, default=0)
    name: Mapped[str] = mapped_column(String, nullable=False)
    team: Mapped[str] = mapped_column(String, default="my")
    birth_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    user_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    age_categories = relationship("PlayerAgeCategoryModel", back_populates="player", cascade="all, delete-orphan")
    events = relationship("EventModel", back_populates="player", cascade="all, delete-orphan")
    roster_entries = relationship("MatchRosterModel", back_populates="player", cascade="all, delete-orphan")


class PlayerAgeCategoryModel(Base):
    __tablename__ = "player_age_categories"
    __table_args__ = (UniqueConstraint("player_id", "age_category"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    player_id: Mapped[str] = mapped_column(String, ForeignKey("players.player_id"), nullable=False)
    age_category: Mapped[str] = mapped_column(String, nullable=False)

    player = relationship("PlayerModel", back_populates="age_categories")


class AgeCategoryModel(Base):
    """Per-club age category dictionary (e.g. U17, Seniorzy)."""
    __tablename__ = "age_categories"
    __table_args__ = (UniqueConstraint("club_id", "name"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    club_id: Mapped[str] = mapped_column(String, ForeignKey("clubs.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class VoiceNoteModel(Base):
    """Audio note attached to a match (optionally a player)."""
    __tablename__ = "voice_notes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    club_id: Mapped[str] = mapped_column(String, ForeignKey("clubs.id"), nullable=False)
    match_id: Mapped[str] = mapped_column(
        String, ForeignKey("matches.match_id", ondelete="CASCADE"), nullable=False
    )
    player_id: Mapped[str | None] = mapped_column(String, nullable=True)
    audio_key: Mapped[str] = mapped_column(String, nullable=False)
    content_type: Mapped[str] = mapped_column(String, default="audio/webm")
    duration_s: Mapped[int] = mapped_column(Integer, default=0)
    note: Mapped[str] = mapped_column(String, default="")
    created_by: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class SubstitutionModel(Base):
    """Player in/out-of-water events for play-time tracking."""
    __tablename__ = "substitutions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    club_id: Mapped[str] = mapped_column(String, ForeignKey("clubs.id"), nullable=False)
    match_id: Mapped[str] = mapped_column(
        String, ForeignKey("matches.match_id", ondelete="CASCADE"), nullable=False
    )
    player_id: Mapped[str] = mapped_column(
        String, ForeignKey("players.player_id", ondelete="CASCADE"), nullable=False
    )
    direction: Mapped[str] = mapped_column(String, nullable=False)  # "in" | "out"
    quarter: Mapped[int] = mapped_column(Integer, default=1)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ──────────────────────── EXISTING: Matches ──────────────────────


class MatchModel(Base):
    __tablename__ = "matches"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    club_id: Mapped[str] = mapped_column(String, ForeignKey("clubs.id"), nullable=False)
    match_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    date: Mapped[str] = mapped_column(String, default="")
    opponent: Mapped[str] = mapped_column(String, default="")
    place: Mapped[str] = mapped_column(String, default="")
    age_category: Mapped[str] = mapped_column(String, default="Seniorzy")
    status: Mapped[str] = mapped_column(String, default="active")
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    season_id: Mapped[str | None] = mapped_column(String, ForeignKey("seasons.id"), nullable=True)
    mvp_player_id: Mapped[str | None] = mapped_column(String, nullable=True)
    # Cumulative quarter scores
    q1_my: Mapped[int] = mapped_column(Integer, default=0)
    q1_opp: Mapped[int] = mapped_column(Integer, default=0)
    q2_my: Mapped[int] = mapped_column(Integer, default=0)
    q2_opp: Mapped[int] = mapped_column(Integer, default=0)
    q3_my: Mapped[int] = mapped_column(Integer, default=0)
    q3_opp: Mapped[int] = mapped_column(Integer, default=0)
    q4_my: Mapped[int] = mapped_column(Integer, default=0)
    q4_opp: Mapped[int] = mapped_column(Integer, default=0)
    final_my: Mapped[int] = mapped_column(Integer, default=0)
    final_opp: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    events = relationship("EventModel", back_populates="match", cascade="all, delete-orphan")
    roster = relationship("MatchRosterModel", back_populates="match", cascade="all, delete-orphan")
    youtube_stream = relationship("YouTubeStreamModel", back_populates="match", uselist=False)


# ──────────────────────── EXISTING: Match Roster ──────────────────────


class MatchRosterModel(Base):
    __tablename__ = "match_roster"
    __table_args__ = (UniqueConstraint("match_id", "player_id"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    club_id: Mapped[str] = mapped_column(String, ForeignKey("clubs.id"), nullable=False)
    match_id: Mapped[str] = mapped_column(String, ForeignKey("matches.match_id", ondelete="CASCADE"), nullable=False)
    player_id: Mapped[str] = mapped_column(String, ForeignKey("players.player_id", ondelete="CASCADE"), nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    team: Mapped[str] = mapped_column(String, default="my")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    match = relationship("MatchModel", back_populates="roster")
    player = relationship("PlayerModel", back_populates="roster_entries")


# ──────────────────────── EXISTING: Events (44 flag columns) ──────────────────────


class EventModel(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    club_id: Mapped[str] = mapped_column(String, ForeignKey("clubs.id"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    match_id: Mapped[str] = mapped_column(String, ForeignKey("matches.match_id", ondelete="CASCADE"), nullable=False)
    quarter: Mapped[int] = mapped_column(Integer, default=1)
    team: Mapped[str] = mapped_column(String, default="my")
    player_id: Mapped[str] = mapped_column(String, ForeignKey("players.player_id", ondelete="CASCADE"), nullable=False)
    player_name: Mapped[str] = mapped_column(String, nullable=False)
    event_type: Mapped[str] = mapped_column(String, default="")
    subtype: Mapped[str] = mapped_column(String, default="")
    value: Mapped[str] = mapped_column(String, default="")
    note: Mapped[str] = mapped_column(String, default="")
    video_timestamp: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ─── ATAK POZYCYJNY (15) ───
    is_goal_from_play_positional: Mapped[int] = mapped_column(Integer, default=0)
    is_goal_from_play_counter: Mapped[int] = mapped_column(Integer, default=0)
    is_goal_from_center_positional: Mapped[int] = mapped_column(Integer, default=0)
    is_assist_positional: Mapped[int] = mapped_column(Integer, default=0)
    is_shot_saved_gk_positional: Mapped[int] = mapped_column(Integer, default=0)
    is_shot_miss_turnover_positional: Mapped[int] = mapped_column(Integer, default=0)
    is_shot_miss_reset30_positional: Mapped[int] = mapped_column(Integer, default=0)
    is_bad_pass_turnover_positional: Mapped[int] = mapped_column(Integer, default=0)
    is_bad_pass_no_turnover_positional: Mapped[int] = mapped_column(Integer, default=0)
    is_turnover_1v1_positional: Mapped[int] = mapped_column(Integer, default=0)
    is_shot_clock_violation_positional: Mapped[int] = mapped_column(Integer, default=0)
    is_excl_drawn_field_positional: Mapped[int] = mapped_column(Integer, default=0)
    is_excl_drawn_center_positional: Mapped[int] = mapped_column(Integer, default=0)
    is_penalty_drawn_field_positional: Mapped[int] = mapped_column(Integer, default=0)
    is_penalty_drawn_center_positional: Mapped[int] = mapped_column(Integer, default=0)

    # ─── ATAK PRZEWAGA (10) ───
    is_goal_from_center_man_up: Mapped[int] = mapped_column(Integer, default=0)
    is_goal_5m_man_up: Mapped[int] = mapped_column(Integer, default=0)
    is_assist_man_up: Mapped[int] = mapped_column(Integer, default=0)
    is_shot_saved_gk_man_up: Mapped[int] = mapped_column(Integer, default=0)
    is_shot_miss_turnover_man_up: Mapped[int] = mapped_column(Integer, default=0)
    is_shot_miss_reset30_man_up: Mapped[int] = mapped_column(Integer, default=0)
    is_bad_pass_turnover_man_up: Mapped[int] = mapped_column(Integer, default=0)
    is_bad_pass_no_turnover_man_up: Mapped[int] = mapped_column(Integer, default=0)
    is_turnover_1v1_man_up: Mapped[int] = mapped_column(Integer, default=0)
    is_shot_clock_violation_man_up: Mapped[int] = mapped_column(Integer, default=0)

    # ─── RZUTY KARNE (1) ───
    is_goal_5m_penalty: Mapped[int] = mapped_column(Integer, default=0)

    # ─── OBRONA POZYCYJNA (9) ───
    is_no_return_positional: Mapped[int] = mapped_column(Integer, default=0)
    is_excl_committed_field_positional: Mapped[int] = mapped_column(Integer, default=0)
    is_excl_committed_center_positional: Mapped[int] = mapped_column(Integer, default=0)
    is_penalty_committed_field_positional: Mapped[int] = mapped_column(Integer, default=0)
    is_penalty_committed_center_positional: Mapped[int] = mapped_column(Integer, default=0)
    is_shot_saved_gk_def_positional: Mapped[int] = mapped_column(Integer, default=0)
    is_steal_positional: Mapped[int] = mapped_column(Integer, default=0)
    is_block_hand_positional: Mapped[int] = mapped_column(Integer, default=0)
    is_no_block_positional: Mapped[int] = mapped_column(Integer, default=0)

    # ─── OBRONA PRZEWAGA (9) ───
    is_no_return_man_up: Mapped[int] = mapped_column(Integer, default=0)
    is_excl_committed_field_man_up: Mapped[int] = mapped_column(Integer, default=0)
    is_excl_committed_center_man_up: Mapped[int] = mapped_column(Integer, default=0)
    is_penalty_committed_field_man_up: Mapped[int] = mapped_column(Integer, default=0)
    is_penalty_committed_center_man_up: Mapped[int] = mapped_column(Integer, default=0)
    is_shot_saved_gk_def_man_up: Mapped[int] = mapped_column(Integer, default=0)
    is_steal_man_up: Mapped[int] = mapped_column(Integer, default=0)
    is_block_hand_man_up: Mapped[int] = mapped_column(Integer, default=0)
    is_no_block_man_up: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    match = relationship("MatchModel", back_populates="events")
    player = relationship("PlayerModel", back_populates="events")


# ──────────────────────── NEW: YouTube Streams ──────────────────────


class YouTubeStreamModel(Base):
    __tablename__ = "youtube_streams"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    match_id: Mapped[str] = mapped_column(String, ForeignKey("matches.match_id", ondelete="CASCADE"), unique=True, nullable=False)
    youtube_url: Mapped[str] = mapped_column(String, nullable=False)
    video_id: Mapped[str] = mapped_column(String, nullable=False)
    stream_start_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    match = relationship("MatchModel", back_populates="youtube_stream")


# ──────────────────────── NEW: Club Config ──────────────────────


class ClubConfigModel(Base):
    __tablename__ = "club_configs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    club_id: Mapped[str] = mapped_column(String, ForeignKey("clubs.id"), unique=True, nullable=False)
    active_modules: Mapped[dict] = mapped_column(JSON, default=list)
    button_layout: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    club = relationship("ClubModel", back_populates="config")
