"""Claude-backed NLU for free-form voice commands.

The deterministic parser (domain/services/voice_command_service) handles the
common, unambiguous cases offline. This adapter is the "smart" layer: it maps
natural phrasings ("dwunastka trafiła z kontry") to the same structured command
using Claude Haiku (fast + cheap). The API key lives server-side.
"""

import json

from src.config import settings
from src.domain.models import EVENT_FLAG_FIELDS
from src.domain.ports.external import ParsedCommand, VoiceCommandPort

_SENTINEL = "none"

_SYSTEM = (
    "Jesteś asystentem statystyk waterpolo. Trener mówi po polsku krótką komendę "
    "opisującą jedno zdarzenie meczowe, np. „numer 12 gol z kontrataku”. "
    "Twoim zadaniem jest zmapować wypowiedź na DOKŁADNIE jedną flagę zdarzenia "
    "oraz numer czepka zawodnika.\n"
    "Zwróć JSON: {\"flag\": <nazwa pola flagi albo \"none\">, "
    "\"number\": <numer czepka jako liczba albo null>, "
    "\"confidence\": <0..1>}.\n"
    "Wybieraj wariant „_man_up” tylko gdy padło słowo o przewadze "
    "(np. „w przewadze”, „z przewagi”). W przeciwnym razie „_positional”. "
    "Gole z kontrataku i karne mają stałe flagi. Jeśli nie rozpoznajesz akcji, "
    'użyj flagi "none".'
)


def _flag_menu(flag_labels: dict[str, str]) -> str:
    return "\n".join(f"- {field}: {label}" for field, label in flag_labels.items())


_SCHEMA = {
    "type": "object",
    "properties": {
        "flag": {"type": "string", "enum": list(EVENT_FLAG_FIELDS) + [_SENTINEL]},
        "number": {"type": ["integer", "null"]},
        "confidence": {"type": "number"},
    },
    "required": ["flag", "number", "confidence"],
    "additionalProperties": False,
}


class ClaudeVoiceCommandAdapter(VoiceCommandPort):
    def __init__(self, api_key: str, model: str):
        self._api_key = api_key
        self._model = model

    async def parse(
        self, transcript: str, numbers: list[int], flag_labels: dict[str, str]
    ) -> ParsedCommand | None:
        try:
            from anthropic import AsyncAnthropic
        except ImportError:
            return None

        client = AsyncAnthropic(api_key=self._api_key)
        roster_hint = (
            f"Numery na liście (skład): {sorted(numbers)}.\n" if numbers else ""
        )
        user = (
            f"{roster_hint}Dostępne flagi (pole: opis):\n{_flag_menu(flag_labels)}\n\n"
            f'Komenda: "{transcript}"'
        )
        try:
            resp = await client.messages.create(
                model=self._model,
                max_tokens=200,
                system=_SYSTEM,
                messages=[{"role": "user", "content": user}],
                output_config={"format": {"type": "json_schema", "schema": _SCHEMA}},
            )
        except Exception:
            return None

        text = "".join(
            b.text for b in resp.content if getattr(b, "type", "") == "text"
        ).strip()
        if not text:
            return None
        try:
            data = json.loads(text)
        except (ValueError, TypeError):
            return None

        flag = data.get("flag")
        if not flag or flag == _SENTINEL or flag not in EVENT_FLAG_FIELDS:
            return None
        number = data.get("number")
        if number is not None:
            try:
                number = int(number)
            except (ValueError, TypeError):
                number = None
        confidence = data.get("confidence")
        try:
            confidence = float(confidence)
        except (ValueError, TypeError):
            confidence = 0.7
        return ParsedCommand(
            flag=flag, number=number, confidence=confidence, source="claude"
        )


def get_voice_command_port() -> VoiceCommandPort | None:
    """Return the Claude NLU adapter when configured, else None (deterministic-only)."""
    if settings.VOICE_NLU_BACKEND != "claude" or not settings.ANTHROPIC_API_KEY:
        return None
    return ClaudeVoiceCommandAdapter(
        api_key=settings.ANTHROPIC_API_KEY, model=settings.ANTHROPIC_NLU_MODEL
    )
