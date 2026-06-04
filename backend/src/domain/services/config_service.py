"""Club configuration service — manage active stat modules per club.

New service from roadmapa Faza 1: konfigurowalny interfejs.
"""

from src.domain.models import EVENT_FLAG_FIELDS
from src.domain.models.config import AVAILABLE_MODULES, ClubConfig

# Mapping: module name -> which flag prefixes belong to it
MODULE_FLAG_PREFIXES: dict[str, list[str]] = {
    "attack_positional": [
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
    ],
    "attack_man_up": [
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
    ],
    "penalties": [
        "is_goal_5m_penalty",
    ],
    "defense_positional": [
        "is_no_return_positional",
        "is_excl_committed_field_positional",
        "is_excl_committed_center_positional",
        "is_penalty_committed_field_positional",
        "is_penalty_committed_center_positional",
        "is_shot_saved_gk_def_positional",
        "is_steal_positional",
        "is_block_hand_positional",
        "is_no_block_positional",
    ],
    "defense_man_up": [
        "is_no_return_man_up",
        "is_excl_committed_field_man_up",
        "is_excl_committed_center_man_up",
        "is_penalty_committed_field_man_up",
        "is_penalty_committed_center_man_up",
        "is_shot_saved_gk_def_man_up",
        "is_steal_man_up",
        "is_block_hand_man_up",
        "is_no_block_man_up",
    ],
}


class ConfigService:
    def get_active_flags(self, config: ClubConfig) -> list[str]:
        """Return only the flag fields that belong to active modules.

        Used by the frontend to filter which stat columns/buttons to show.
        """
        active_flags: list[str] = []
        for module in config.active_modules:
            if module in MODULE_FLAG_PREFIXES:
                active_flags.extend(MODULE_FLAG_PREFIXES[module])
        return active_flags

    def validate_modules(self, modules: list[str]) -> list[str]:
        """Filter out invalid module names."""
        return [m for m in modules if m in AVAILABLE_MODULES]
