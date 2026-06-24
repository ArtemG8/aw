from aiogram import Router

from handlers.admin_handlers import router as admin_router
from handlers.admin_handlers import set_admin_menu
from handlers.user_handlers import router as user_router


def setup_routers() -> Router:
    root_router = Router()
    root_router.include_router(admin_router)
    root_router.include_router(user_router)
    return root_router


__all__ = ("setup_routers", "set_admin_menu")
