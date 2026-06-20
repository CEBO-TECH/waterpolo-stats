"""Deterministic voice-command parser — Polish utterance → flag + cap number."""

import pytest

from src.domain.models import EVENT_FLAG_FIELDS
from src.domain.services import VoiceCommandService

svc = VoiceCommandService()


@pytest.mark.parametrize(
    "transcript,flag,number",
    [
        ("numer dwanaście gol z kontrataku", "is_goal_from_play_counter", 12),
        ("siódemka asysta", "is_assist_positional", 7),
        ("5 obrona bramkarza", "is_shot_saved_gk_positional", 5),
        ("numer 4 gol z przewagi z centra", "is_goal_from_center_man_up", 4),
        ("dziewiątka przejęcie", "is_steal_positional", 9),
        ("gol numer 10", "is_goal_from_play_positional", 10),
        ("jedenastka asysta w przewadze", "is_assist_man_up", 11),
        ("numer 6 gol z karnego", "is_goal_5m_penalty", 6),
        ("ósemka sprowadziła wykluczenie", "is_excl_drawn_field_positional", 8),
        ("numer trzy blok", "is_block_hand_positional", 3),
    ],
)
def test_parses_common_commands(transcript, flag, number):
    cmd = svc.parse(transcript)
    assert cmd is not None, transcript
    assert cmd.flag == flag
    assert cmd.number == number
    assert cmd.flag in EVENT_FLAG_FIELDS
    assert cmd.confidence >= 0.9
    assert cmd.source == "deterministic"


def test_action_without_number_low_confidence():
    cmd = svc.parse("gol z akcji")
    assert cmd is not None
    assert cmd.number is None
    assert cmd.confidence < 0.9


def test_unrecognised_returns_none():
    assert svc.parse("dzień dobry jak leci") is None
    assert svc.parse("") is None
