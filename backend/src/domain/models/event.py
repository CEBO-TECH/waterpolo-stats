from dataclasses import dataclass, field
from datetime import datetime


# Single source of truth for all 44 event flag field names.
# Order matters — matches the original Prisma schema and stats aggregation.
EVENT_FLAG_FIELDS: tuple[str, ...] = (
    # ATAK POZYCYJNY (15)
    "is_goal_from_play_positional",
    "is_goal_from_play_counter",
    "is_goal_from_center_positional",
    "is_assist_positional",
    "is_shot_saved_gk_positional",
    "is_shot_miss_turnover_positional",
    "is_shot_miss_reset30_positional",
    "is_bad_pass_turnover_positional",
    "is_bad_pass_no_turnover_positional",
    "is_turnover_1v1_positional",
    "is_shot_clock_violation_positional",
    "is_excl_drawn_field_positional",
    "is_excl_drawn_center_positional",
    "is_penalty_drawn_field_positional",
    "is_penalty_drawn_center_positional",
    # ATAK PRZEWAGA (10)
    "is_goal_from_center_man_up",
    "is_goal_5m_man_up",
    "is_assist_man_up",
    "is_shot_saved_gk_man_up",
    "is_shot_miss_turnover_man_up",
    "is_shot_miss_reset30_man_up",
    "is_bad_pass_turnover_man_up",
    "is_bad_pass_no_turnover_man_up",
    "is_turnover_1v1_man_up",
    "is_shot_clock_violation_man_up",
    # RZUTY KARNE (1)
    "is_goal_5m_penalty",
    # OBRONA POZYCYJNA (9)
    "is_no_return_positional",
    "is_excl_committed_field_positional",
    "is_excl_committed_center_positional",
    "is_penalty_committed_field_positional",
    "is_penalty_committed_center_positional",
    "is_shot_saved_gk_def_positional",
    "is_steal_positional",
    "is_block_hand_positional",
    "is_no_block_positional",
    # OBRONA PRZEWAGA (9)
    "is_no_return_man_up",
    "is_excl_committed_field_man_up",
    "is_excl_committed_center_man_up",
    "is_penalty_committed_field_man_up",
    "is_penalty_committed_center_man_up",
    "is_shot_saved_gk_def_man_up",
    "is_steal_man_up",
    "is_block_hand_man_up",
    "is_no_block_man_up",
)

# Polish labels for each flag. Port of getEventAction() from
# app/api/events/[matchId]/route.ts:42-149
EVENT_FLAG_LABELS: dict[str, str] = {
    "is_goal_from_play_positional": "G z akcji (poz.)",
    "is_goal_from_play_counter": "G z kontrataku",
    "is_goal_from_center_positional": "G z centra (poz.)",
    "is_goal_from_center_man_up": "G z centra (przew.)",
    "is_goal_5m_man_up": "G z 5m (przew.)",
    "is_goal_5m_penalty": "G z karnego",
    "is_assist_positional": "Asysta (poz.)",
    "is_assist_man_up": "Asysta (przew.)",
    "is_shot_saved_gk_positional": "Obrona GK (poz.)",
    "is_shot_saved_gk_man_up": "Obrona GK (przew.)",
    "is_shot_miss_turnover_positional": "Niecelny rzut - strata (poz.)",
    "is_shot_miss_turnover_man_up": "Niecelny rzut - strata (przew.)",
    "is_shot_miss_reset30_positional": "Niecelny rzut - 30s (poz.)",
    "is_shot_miss_reset30_man_up": "Niecelny rzut - 30s (przew.)",
    "is_bad_pass_turnover_positional": "Złe podanie - strata (poz.)",
    "is_bad_pass_turnover_man_up": "Złe podanie - strata (przew.)",
    "is_bad_pass_no_turnover_positional": "Złe podanie - bez straty (poz.)",
    "is_bad_pass_no_turnover_man_up": "Złe podanie - bez straty (przew.)",
    "is_turnover_1v1_positional": "Strata 1:1 (poz.)",
    "is_turnover_1v1_man_up": "Strata 1:1 (przew.)",
    "is_shot_clock_violation_positional": "Koniec czasu (poz.)",
    "is_shot_clock_violation_man_up": "Koniec czasu (przew.)",
    "is_excl_drawn_field_positional": "Sprow. wykl. - w polu (poz.)",
    "is_excl_drawn_center_positional": "Sprow. wykl. - z centra (poz.)",
    "is_penalty_drawn_field_positional": "Sprow. karny - w polu (poz.)",
    "is_penalty_drawn_center_positional": "Sprow. karny - z centra (poz.)",
    "is_no_return_positional": "Brak powrotu (poz.)",
    "is_no_return_man_up": "Brak powrotu (przew.)",
    "is_excl_committed_field_positional": "Wykl. spowod. - w polu (poz.)",
    "is_excl_committed_field_man_up": "Wykl. spowod. - w polu (przew.)",
    "is_excl_committed_center_positional": "Wykl. spowod. - z centra (poz.)",
    "is_excl_committed_center_man_up": "Wykl. spowod. - z centra (przew.)",
    "is_penalty_committed_field_positional": "Karny spowod. - w polu (poz.)",
    "is_penalty_committed_field_man_up": "Karny spowod. - w polu (przew.)",
    "is_penalty_committed_center_positional": "Karny spowod. - z centra (poz.)",
    "is_penalty_committed_center_man_up": "Karny spowod. - z centra (przew.)",
    "is_shot_saved_gk_def_positional": "Obrona GK def (poz.)",
    "is_shot_saved_gk_def_man_up": "Obrona GK def (przew.)",
    "is_steal_positional": "Przejęcie (poz.)",
    "is_steal_man_up": "Przejęcie (przew.)",
    "is_block_hand_positional": "Blok (poz.)",
    "is_block_hand_man_up": "Blok (przew.)",
    "is_no_block_positional": "Brak bloku (poz.)",
    "is_no_block_man_up": "Brak bloku (przew.)",
}


@dataclass
class Event:
    id: str
    club_id: str
    match_id: str
    player_id: str
    player_name: str
    quarter: int = 1
    team: str = "my"
    event_type: str = ""
    subtype: str = ""
    value: str = ""
    note: str = ""
    video_timestamp: int | None = None  # Seconds from stream start
    timestamp: datetime = field(default_factory=datetime.utcnow)
    # 44 binary flag fields — all default to 0
    # ATAK POZYCYJNY (15)
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
    # ATAK PRZEWAGA (10)
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
    # RZUTY KARNE (1)
    is_goal_5m_penalty: int = 0
    # OBRONA POZYCYJNA (9)
    is_no_return_positional: int = 0
    is_excl_committed_field_positional: int = 0
    is_excl_committed_center_positional: int = 0
    is_penalty_committed_field_positional: int = 0
    is_penalty_committed_center_positional: int = 0
    is_shot_saved_gk_def_positional: int = 0
    is_steal_positional: int = 0
    is_block_hand_positional: int = 0
    is_no_block_positional: int = 0
    # OBRONA PRZEWAGA (9)
    is_no_return_man_up: int = 0
    is_excl_committed_field_man_up: int = 0
    is_excl_committed_center_man_up: int = 0
    is_penalty_committed_field_man_up: int = 0
    is_penalty_committed_center_man_up: int = 0
    is_shot_saved_gk_def_man_up: int = 0
    is_steal_man_up: int = 0
    is_block_hand_man_up: int = 0
    is_no_block_man_up: int = 0

    def get_flag_value(self, flag_name: str) -> int:
        """Get the value of a flag field by name."""
        return getattr(self, flag_name, 0)

    def get_flag_values(self) -> dict[str, int]:
        """Get all 44 flag values as a dict."""
        return {flag: self.get_flag_value(flag) for flag in EVENT_FLAG_FIELDS}
