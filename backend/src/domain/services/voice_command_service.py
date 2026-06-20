"""Deterministic voice-command parser (offline, instant, no API).

Maps a Polish utterance like "numer dwanaście gol z kontrataku" to a single
event flag (`is_goal_from_play_counter`) plus the cap number (12). This is the
reliable core of the voice agent — the Claude layer (adapters/ai) only kicks in
when this returns nothing actionable or fails to find a number.
"""

import re

from src.domain.models import EVENT_FLAG_FIELDS
from src.domain.ports.external import ParsedCommand

# --- diacritics folding so tables/inputs match regardless of ASR encoding ---

_FOLD = str.maketrans("ąćęłńóśźż", "acelnoszz")


def _norm(text: str) -> str:
    return text.lower().translate(_FOLD)


# --- number words (cap numbers 0-30), folded to ASCII ---

_UNITS = {
    "zero": 0, "jeden": 1, "jedna": 1, "dwa": 2, "dwie": 2, "trzy": 3,
    "cztery": 4, "piec": 5, "szesc": 6, "siedem": 7, "osiem": 8, "dziewiec": 9,
    "dziesiec": 10, "jedenascie": 11, "dwanascie": 12, "trzynascie": 13,
    "czternascie": 14, "pietnascie": 15, "szesnascie": 16, "siedemnascie": 17,
    "osiemnascie": 18, "dziewietnascie": 19, "dwadziescia": 20,
}
# "-ka" / nickname forms a coach actually says ("dwunastka", "piatka", ...)
_NICK = {
    "jedynka": 1, "dwojka": 2, "trojka": 3, "czworka": 4, "piatka": 5,
    "szostka": 6, "siodemka": 7, "osemka": 8, "dziewiatka": 9, "dziesiatka": 10,
    "jedenastka": 11, "dwunastka": 12, "trzynastka": 13, "czternastka": 14,
    "pietnastka": 15, "szesnastka": 16, "siedemnastka": 17, "osiemnastka": 18,
    "dziewietnastka": 19, "dwudziestka": 20,
}


def _extract_number(tokens: list[str], raw: str) -> int | None:
    # digits win ("numer 12", "12")
    m = re.search(r"\b(\d{1,2})\b", raw)
    if m:
        return int(m.group(1))
    # nickname forms first ("dwunastka")
    for t in tokens:
        if t in _NICK:
            return _NICK[t]
    # plain number words, incl. "dwadziescia jeden" -> 21
    for i, t in enumerate(tokens):
        if t == "dwadziescia" and i + 1 < len(tokens) and tokens[i + 1] in _UNITS:
            nxt = _UNITS[tokens[i + 1]]
            if 1 <= nxt <= 9:
                return 20 + nxt
        if t in _UNITS:
            return _UNITS[t]
    return None


def _has(raw: str, *needles: str) -> bool:
    return any(n in raw for n in needles)


class VoiceCommandService:
    """Rule-based mapping from spoken Polish to an event flag + cap number."""

    def parse(self, transcript: str) -> ParsedCommand | None:
        raw = _norm(transcript)
        if not raw.strip():
            return None
        tokens = re.findall(r"[a-z0-9]+", raw)
        number = _extract_number(tokens, raw)

        is_man_up = _has(raw, "przewag", "przewadze", "man up", "manap", "gora")
        suffix = "man_up" if is_man_up else "positional"

        flag = self._match_action(raw, suffix)
        if not flag:
            return None
        # honour the schema: fall back to positional if a man_up variant is absent
        if flag not in EVENT_FLAG_FIELDS:
            alt = flag.replace("_man_up", "_positional")
            flag = alt if alt in EVENT_FLAG_FIELDS else None
        if not flag:
            return None

        # action + number = high confidence; action only = let Claude try the number
        confidence = 0.95 if number is not None else 0.55
        return ParsedCommand(flag=flag, number=number, confidence=confidence)

    def _match_action(self, raw: str, suffix: str) -> str | None:
        # --- goals (most specific first) ---
        # NB: deliberately not "bramk" — it collides with "bramkarz" (goalkeeper)
        # and "obok/mimo bramki" (missed shot).
        if _has(raw, "gol", "trafi", "strzeli", "zdobyl"):
            if _has(raw, "kontr"):
                return "is_goal_from_play_counter"
            if _has(raw, "karn", "rzut karny", "z karnego"):
                return "is_goal_5m_penalty"
            if _has(raw, "centr", "podkosz", "z dolka", "dolek"):
                return f"is_goal_from_center_{suffix}"
            if _has(raw, "5m", "piec metr", "piatk", "rzut z piec"):
                return "is_goal_5m_man_up"
            return f"is_goal_from_play_{suffix}"

        # --- assist ---
        if _has(raw, "asyst", "podanie do bramki", "dogral"):
            return f"is_assist_{suffix}"

        # --- penalties drawn / committed (before generic "karny") ---
        if _has(raw, "karn"):
            if _has(raw, "spowod", "faul", "przewini", "zlapal", "popelni"):
                base = "is_penalty_committed_center" if _has(raw, "centr") else "is_penalty_committed_field"
                return f"{base}_{suffix}"
            base = "is_penalty_drawn_center" if _has(raw, "centr") else "is_penalty_drawn_field"
            return f"{base}_positional"

        # --- exclusions drawn / committed ---
        if _has(raw, "wyklucz", "wykluczen", "wykl", "wyrzuc"):
            if _has(raw, "spowod", "faul", "przewini", "popelni", "na nim wykl"):
                base = "is_excl_committed_center" if _has(raw, "centr") else "is_excl_committed_field"
                return f"{base}_{suffix}"
            base = "is_excl_drawn_center" if _has(raw, "centr") else "is_excl_drawn_field"
            return f"{base}_positional"

        # --- steal / block / no-block ---
        if _has(raw, "brak bloku", "bez bloku", "nie zablok"):
            return f"is_no_block_{suffix}"
        if _has(raw, "blok", "zablok"):
            return f"is_block_hand_{suffix}"
        if _has(raw, "przejec", "przechwyt", "odebra", "przejal"):
            return f"is_steal_{suffix}"

        # --- no return (transition defence) ---
        if _has(raw, "brak powrotu", "nie wroci", "bez powrotu", "nie cofnal"):
            return f"is_no_return_{suffix}"

        # --- goalkeeper saves (defence variant if "nasz"/"obrona"/"def") ---
        if _has(raw, "obron", "obroni", "wybroni"):
            if _has(raw, "nasz", "def", "w obronie", "nasza bramk"):
                return f"is_shot_saved_gk_def_{suffix}"
            return f"is_shot_saved_gk_{suffix}"

        # --- missed shots ---
        if _has(raw, "niecel", "pudl", "spudl", "mimo bramki", "obok bramki", "minal"):
            if _has(raw, "30", "trzydziest", "powtor", "reset"):
                return f"is_shot_miss_reset30_{suffix}"
            return f"is_shot_miss_turnover_{suffix}"

        # --- bad pass / turnover ---
        if _has(raw, "zle podanie", "zla podanie", "spudlowane podanie", "podanie w aut"):
            if _has(raw, "bez straty", "nie stracil", "utrzymal"):
                return f"is_bad_pass_no_turnover_{suffix}"
            return f"is_bad_pass_turnover_{suffix}"
        if _has(raw, "jeden na jeden", "1 na 1", "1v1", "jeden_na_jeden"):
            return f"is_turnover_1v1_{suffix}"
        if _has(raw, "koniec czasu", "30 sekund", "czas akcji", "shot clock"):
            return f"is_shot_clock_violation_{suffix}"
        if _has(raw, "strat", "stracil", "zgubil pilk", "utrata"):
            return f"is_turnover_1v1_{suffix}"

        return None
