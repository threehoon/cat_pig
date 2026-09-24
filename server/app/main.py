import pkgutil
from importlib import import_module, util

from fastapi import APIRouter, FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app import modules
from app.core.envelope import DataEnvelope
from app.core.exceptions import register_exception_handlers
from app.core.settings import get_settings


class HealthData(BaseModel):
    ok: bool


def include_module_routers(app: FastAPI) -> None:
    prefix = f"{modules.__name__}."
    for module_info in pkgutil.iter_modules(modules.__path__, prefix):
        if not module_info.ispkg:
            continue

        router_name = f"{module_info.name}.router"
        if util.find_spec(router_name) is None:
            continue

        router_module = import_module(router_name)
        router = getattr(router_module, "router", None)
        if not isinstance(router, APIRouter):
            raise RuntimeError(f"{router_name} must expose an APIRouter named router")

        feature = module_info.name.rsplit(".", maxsplit=1)[-1]
        app.include_router(router, prefix=f"/api/v1/{feature}")


def create_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/health")
    def health() -> DataEnvelope[HealthData]:
        return DataEnvelope(data=HealthData(ok=True))

    include_module_routers(app)
    media_root = get_settings().media_root
    media_root.mkdir(parents=True, exist_ok=True)
    app.mount("/media", StaticFiles(directory=media_root), name="media")
    return app


app = create_app()
