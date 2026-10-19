import hashlib

from django.conf import settings
from django.core.cache import cache

from .geo import cumulative_miles, stations_near_route, thin_route
from .planner import plan_fuel_stops
from .services import fetch_route, geocode
from .stations import get_stations


def build_plan(start, finish):
    key = "plan:" + hashlib.md5(f"{start.lower()}|{finish.lower()}".encode()).hexdigest()
    hit = cache.get(key)
    if hit:
        return hit

    a, b = geocode(start), geocode(finish)
    coords, miles = fetch_route(a, b)
    cum = cumulative_miles(coords, miles)
    pts, pcum = thin_route(coords, cum)

    st = get_stations()
    idx, marks, _ = stations_near_route(pts, pcum, st["xyz"], settings.MAX_OFF_ROUTE_MILES)
    cands = [{**st["rows"][i], "route_mile": float(m)} for i, m in zip(idx, marks)]

    stops, cost = plan_fuel_stops(cands, miles, settings.VEHICLE_RANGE_MILES, settings.VEHICLE_MPG)

    result = {
        "start": {"query": start, "lat": a[0], "lon": a[1]},
        "finish": {"query": finish, "lat": b[0], "lon": b[1]},
        "distance_miles": round(miles, 1),
        "fuel_stops": [
            {
                "name": x["station"]["name"],
                "address": x["station"]["address"],
                "city": x["station"]["city"],
                "state": x["station"]["state"],
                "lat": x["station"]["lat"],
                "lon": x["station"]["lon"],
                "route_mile": round(x["station"]["route_mile"], 1),
                "price_per_gallon": round(x["station"]["price"], 3),
                "gallons_purchased": round(x["gallons"], 2),
                "cost": round(x["cost"], 2),
            }
            for x in stops
        ],
        "total_gallons_purchased": round(sum(x["gallons"] for x in stops), 2),
        "total_fuel_cost": cost,
        "assumptions": {
            "range_miles": settings.VEHICLE_RANGE_MILES,
            "mpg": settings.VEHICLE_MPG,
            "starts_with_full_tank": True,
        },
        "route": {
            "type": "Feature",
            "properties": {},
            "geometry": {"type": "LineString", "coordinates": pts.round(5).tolist()},
        },
    }
    cache.set(key, result, settings.CACHE_SECONDS)
    return result