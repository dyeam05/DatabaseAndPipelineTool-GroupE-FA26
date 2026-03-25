import re

_PATTERN = re.compile(r"^[^|]+\|[^-]+--[^/]+$")


def is_valid_route_str(s: str) -> bool:
    return bool(_PATTERN.match(s))

def get_open_pilot_device_name_from_route_str(route_str: str):
    if not is_valid_route_str(route_str):
        raise ValueError(f"Invalid route string. Route string should look something like this: db478799b6f9f210|00000044--2b2126c478, but not this: db478799b6f9f210|00000044--2b2126c478/10")

    return route_str.split("|")[0]