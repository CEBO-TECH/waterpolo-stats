"""Club config routes — manage active stat modules per club."""

from fastapi import APIRouter
from pydantic import BaseModel

from src.api.deps import AnyMember, ConfigRepo, OwnerOnly
from src.domain.services import ConfigService

router = APIRouter(prefix="/v1/clubs/{club_id}/config", tags=["config"])
config_service = ConfigService()


class ConfigUpdateRequest(BaseModel):
    active_modules: list[str]
    button_layout: dict = {}


@router.get("")
async def get_config(club_id: str, ctx: AnyMember, repo: ConfigRepo):
    config = await repo.get_for_club(club_id)
    return {
        "active_modules": config.active_modules,
        "button_layout": config.button_layout,
        "active_flags": config_service.get_active_flags(config),
    }


@router.put("")
async def update_config(
    club_id: str, body: ConfigUpdateRequest, ctx: OwnerOnly, repo: ConfigRepo,
):
    config = await repo.get_for_club(club_id)
    config.active_modules = config_service.validate_modules(body.active_modules)
    config.button_layout = body.button_layout
    updated = await repo.update(config)
    return {
        "active_modules": updated.active_modules,
        "button_layout": updated.button_layout,
        "active_flags": config_service.get_active_flags(updated),
    }
