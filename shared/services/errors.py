class RouteAlreadyExistsError(ValueError):
    def __init__(self, route_id: str) -> None:
        super().__init__(f"Route {route_id} already exists")


class RouteNotFoundError(ValueError):
    def __init__(self, route_id: str) -> None:
        super().__init__(f"Route {route_id} not found")
