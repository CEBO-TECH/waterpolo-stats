"""Event action label resolution.

Port of getEventAction() from app/api/events/[matchId]/route.ts:42-149.
"""

from src.domain.models import EVENT_FLAG_FIELDS, EVENT_FLAG_LABELS, Event


class EventService:
    def get_event_action(self, event: Event) -> str:
        """Return the Polish label for the first non-zero flag on an event.

        Iterates through all 44 flags in order and returns the label
        for the first flag that equals 1. Falls back to "Nieznana akcja".
        """
        for flag in EVENT_FLAG_FIELDS:
            if event.get_flag_value(flag) == 1:
                return EVENT_FLAG_LABELS.get(flag, flag)
        return "Nieznana akcja"

    def format_recent_event(self, event: Event) -> dict:
        """Format an event for the recent events list display."""
        return {
            "id": event.id,
            "timestamp": event.timestamp.isoformat(),
            "quarter": event.quarter,
            "player_name": event.player_name,
            "event_type": event.event_type,
            "note": event.note,
            "action": self.get_event_action(event),
        }
