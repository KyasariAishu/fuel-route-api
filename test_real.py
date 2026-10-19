import numpy as np
from routing.services import geocode, fetch_route
from routing.geo import cumulative_miles, thin_route, stations_near_route
from routing.stations import get_stations
from routing.planner import plan_fuel_stops

a, b = geocode("Chicago, IL"), geocode("Dallas, TX")
coords, miles = fetch_route(a, b)
cum = cumulative_miles(coords, miles)
pts, pcum = thin_route(coords, cum)
st = get_stations()
idx, mile_marks, off = stations_near_route(pts, pcum, st["xyz"])

print(mile_marks)

cands = [{**st["rows"][i], "route_mile": float(m)} for i, m in zip(idx, mile_marks)]
stops, cost = plan_fuel_stops(cands, miles)

print("total cost:", cost, "| stops:", len(stops))
for x in stops:
    r = x["station"]
    print(round(r["route_mile"]), "mi", r["name"], r["city"], r["state"], r["price"], round(x["gallons"], 1), "gal", round(x["cost"], 2))