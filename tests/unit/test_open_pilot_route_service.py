import pytest


from services.open_pilot_route_service import OpenPilotRouteService

@pytest.mark.asyncio
async def test_get_route_metadata():
    route_name = "db478799b6f9f210|00000044--2b2126c478"

    open_pilot_route_service = OpenPilotRouteService()
    metadata = await open_pilot_route_service.get_route_metadata(route_name=route_name)
    assert metadata is not None, "metadata should not be None. Make sure your open pilot JWT is correct"
    assert metadata.fullname == route_name, "Metadata full name should be the same as route name"

    