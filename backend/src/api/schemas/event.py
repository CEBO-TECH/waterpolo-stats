from pydantic import BaseModel


class EventCreate(BaseModel):
    match_id: str | None = None
    quarter: int | None = None
    team: str = "my"
    player_id: str
    player_name: str
    event_type: str = ""
    subtype: str = ""
    value: str = ""
    note: str = ""
    # Optional ISO event time. Defaults to "now"; pass it to backfill historical
    # events so the YouTube replay seek lands on the right moment.
    timestamp: str | None = None
    # All 44 flags default to 0
    is_goal_from_play_positional: int = 0
    is_goal_from_play_counter: int = 0
    is_goal_from_center_positional: int = 0
    is_assist_positional: int = 0
    is_shot_saved_gk_positional: int = 0
    is_shot_miss_turnover_positional: int = 0
    is_shot_miss_reset30_positional: int = 0
    is_bad_pass_turnover_positional: int = 0
    is_bad_pass_no_turnover_positional: int = 0
    is_turnover_1v1_positional: int = 0
    is_shot_clock_violation_positional: int = 0
    is_excl_drawn_field_positional: int = 0
    is_excl_drawn_center_positional: int = 0
    is_penalty_drawn_field_positional: int = 0
    is_penalty_drawn_center_positional: int = 0
    is_goal_from_center_man_up: int = 0
    is_goal_5m_man_up: int = 0
    is_assist_man_up: int = 0
    is_shot_saved_gk_man_up: int = 0
    is_shot_miss_turnover_man_up: int = 0
    is_shot_miss_reset30_man_up: int = 0
    is_bad_pass_turnover_man_up: int = 0
    is_bad_pass_no_turnover_man_up: int = 0
    is_turnover_1v1_man_up: int = 0
    is_shot_clock_violation_man_up: int = 0
    is_goal_5m_penalty: int = 0
    is_no_return_positional: int = 0
    is_excl_committed_field_positional: int = 0
    is_excl_committed_center_positional: int = 0
    is_penalty_committed_field_positional: int = 0
    is_penalty_committed_center_positional: int = 0
    is_shot_saved_gk_def_positional: int = 0
    is_steal_positional: int = 0
    is_block_hand_positional: int = 0
    is_no_block_positional: int = 0
    is_no_return_man_up: int = 0
    is_excl_committed_field_man_up: int = 0
    is_excl_committed_center_man_up: int = 0
    is_penalty_committed_field_man_up: int = 0
    is_penalty_committed_center_man_up: int = 0
    is_shot_saved_gk_def_man_up: int = 0
    is_steal_man_up: int = 0
    is_block_hand_man_up: int = 0
    is_no_block_man_up: int = 0


class EventBatchCreate(BaseModel):
    events: list[EventCreate]


class EventResponse(BaseModel):
    id: str
    timestamp: str
    quarter: int
    player_name: str
    event_type: str
    note: str
    action: str  # Human-readable Polish label


class UndoRequest(BaseModel):
    window_minutes: int = 3
