import requests
from datetime import datetime
from zoneinfo import ZoneInfo


JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3ODIwMDEzOTEsIm5iZiI6MTc3NDIyNTM5MSwiaWF0IjoxNzc0MjI1MzkxLCJpZGVudGl0eSI6IjJjMTY4NTM5NTgwZWIyNjYifQ.6Pb8oOFJ4Mw1remBwj7MOizK7e1wX9rHtoiyZFVf_Tw"

DONGLE_ID = "db478799b6f9f210"
headers = {"Authorization": f"JWT {JWT_TOKEN}"}

headers = {"Authorization": f"JWT {JWT_TOKEN}"}

routes_resp = requests.get(
    f"https://api.commadotai.com/v1/devices/{DONGLE_ID}/routes",
    headers=headers,
)
routes_resp.raise_for_status()

route0 = routes_resp.json()[0]
route_str = route0["fullname"]

# These strings appear naive, so assign the route's likely local timezone explicitly.
# Change this if you know the route was recorded in a different timezone.
tz = ZoneInfo("America/Chicago")

start_ms = int(
    datetime.fromisoformat(route0["start_time"]).replace(tzinfo=tz).timestamp() * 1000
)
end_ms = int(
    datetime.fromisoformat(route0["end_time"]).replace(tzinfo=tz).timestamp() * 1000
)


resp = requests.get(
    f"https://api.commadotai.com/v1/devices/{DONGLE_ID}/routes_segments",
    headers=headers,
    params={
        "start": 0,
        "end": end_ms,
    },
)
# print("URL:", resp.url)
# print("status:", resp.status_code)
# print("body:", resp.text)
print(resp.json()[0])
