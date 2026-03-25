import pytest

from services.open_pilot_route_service import OpenPilotRouteService
from utilities.open_pilot_utilities import is_valid_route_str


def test_invalid_route_string_with_segment_suffix():
    invalid_route = "db478799b6f9f210|00000044--2b2126c478/10"

    assert not is_valid_route_str(invalid_route)

def test_valid_route_string():
    valid_route = "db478799b6f9f210|00000044--2b2126c478"
    assert is_valid_route_str(valid_route)