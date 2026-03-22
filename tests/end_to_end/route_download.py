import time
import warnings

import pytest
import requests


BASE_URL = "http://localhost:8000"
ROUTES_URL = f"{BASE_URL}/routes"

ROUTE_PREFIX = "db478799b6f9f210/00000040--8afe968813"
ROUTE_SUFFIXES = [20, 21, 22]
EXPECTED_STATUS = "upload queue"

POLL_INTERVAL_SECONDS = 5
TIMEOUT_SECONDS = 6 * 60


def post_route(route_id: str) -> None:
    payload: dict[str, str] = {
        "route_id": route_id,
        "status": "download queue",
    }

    response = requests.post(
        ROUTES_URL,
        headers={
            "accept": "application/json",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )

    assert response.status_code in {200, 201}, (
        f"POST failed for {route_id}: "
        f"status={response.status_code}, body={response.text}"
    )


def get_routes() -> list[dict]:
    response = requests.get(
        ROUTES_URL,
        headers={"accept": "application/json"},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    if not isinstance(data, list):
        raise AssertionError(f"Expected list response, got {type(data).__name__}")

    return data


@pytest.mark.integration
def test_routes_eventually_reach_upload_queue() -> None:
    # Explicit runtime warning
    warnings.warn(
        "This test requires the backend, database, and OpenPilot download worker "
        "containers to be running. Ensure docker compose services are up.",
        RuntimeWarning,
    )

    target_route_ids = [f"{ROUTE_PREFIX}/{suffix}" for suffix in ROUTE_SUFFIXES]

    # Step 1: create routes
    for route_id in target_route_ids:
        post_route(route_id)

    # Step 2: poll for status transition
    deadline = time.monotonic() + TIMEOUT_SECONDS
    last_seen_routes: dict[str, dict] = {}

    while time.monotonic() < deadline:
        routes = get_routes()

        route_map = {r["route_id"]: r for r in routes if "route_id" in r}

        last_seen_routes = {
            rid: route_map[rid]
            for rid in target_route_ids
            if rid in route_map
        }

        all_present = len(last_seen_routes) == len(target_route_ids)
        all_upload_queued = all(
            r.get("status") == EXPECTED_STATUS
            for r in last_seen_routes.values()
        )

        if all_present and all_upload_queued:
            return

        time.sleep(POLL_INTERVAL_SECONDS)

    # Failure diagnostics
    missing = [
        rid for rid in target_route_ids
        if rid not in last_seen_routes
    ]

    statuses = {
        rid: last_seen_routes[rid].get("status")
        for rid in last_seen_routes
    }

    pytest.fail(
        "Timed out waiting for routes to reach 'upload queue'.\n"
        f"Missing: {missing}\n"
        f"Last seen statuses: {statuses}"
    )