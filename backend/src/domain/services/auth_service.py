"""Authorization service — role-based access control."""

from src.domain.models import ClubMembership, UserRole


class AuthService:
    """Determines which actions each role can perform within a club."""

    ROLE_PERMISSIONS: dict[UserRole, set[str]] = {
        UserRole.OWNER: {
            "manage_club",
            "manage_config",
            "invite_users",
            "manage_seasons",
            "manage_players",
            "manage_matches",
            "record_events",
            "view_stats",
        },
        UserRole.COACH: {
            "manage_players",
            "manage_matches",
            "record_events",
            "view_stats",
        },
        UserRole.PLAYER: {
            "view_stats",
        },
    }

    def can_perform(self, membership: ClubMembership, action: str) -> bool:
        """Check if a club member has permission to perform an action."""
        permissions = self.ROLE_PERMISSIONS.get(membership.role, set())
        return action in permissions

    def get_minimum_role(self, action: str) -> UserRole | None:
        """Get the minimum role required for an action."""
        for role in (UserRole.PLAYER, UserRole.COACH, UserRole.OWNER):
            if action in self.ROLE_PERMISSIONS.get(role, set()):
                return role
        return None
