"""Module auto-discovery, so nobody has to edit `main.py` to add a module, route or model.

Convention for `app/modules/<name>/`:
    router.py  -> exposes `router: APIRouter`   (mounted under /api)
    models.py  -> SQLAlchemy models inheriting from `app.core.db.Base` (picked up by Alembic)
"""

import importlib
import pkgutil

from fastapi import APIRouter

import app.modules as modules_pkg


def _module_names() -> list[str]:
    return sorted(m.name for m in pkgutil.iter_modules(modules_pkg.__path__) if m.ispkg)


def _try_import(name: str):
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as e:
        # Missing file -> skip it. Any other import error inside the module is a real bug: re-raise.
        if e.name == name:
            return None
        raise


def discover_routers() -> list[APIRouter]:
    routers = []
    for name in _module_names():
        mod = _try_import(f"app.modules.{name}.router")
        if mod is not None and isinstance(getattr(mod, "router", None), APIRouter):
            routers.append(mod.router)
    return routers


def import_all_models() -> None:
    """Called from `migrations/env.py` so `Base.metadata` contains the tables of every module."""
    for name in _module_names():
        _try_import(f"app.modules.{name}.models")
