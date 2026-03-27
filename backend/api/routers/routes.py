import logging

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, FastAPI, Request, Response, status, APIRouter

from backend.api.dependencies import get_session
from db.enums import RouteStatus
from db.models.route import Route
from schemas.route import CreateRouteRequest, RouteResponse
from services.route_service import RouteService
from utilities.service_builder_utilities import build_route_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

routes_router = APIRouter(
    prefix="/routes",
)

@routes_router.get("/")
async def list_routes(
    session: AsyncSession = Depends(get_session),
) -> list[Route]:
    logging.info("get routes")
    route_service = build_route_service(session=session)
    return await route_service.list_routes()

@routes_router.post("/", response_model=RouteResponse, status_code=status.HTTP_201_CREATED)
async def create_route(
    payload: CreateRouteRequest,
    session: AsyncSession = Depends(get_session)
) -> Route:
    route_service: RouteService = build_route_service(session=session)
    return await route_service.create_route(
        route_id=payload.route_id,
        status=RouteStatus.DOWNLOAD_QUEUE
    )