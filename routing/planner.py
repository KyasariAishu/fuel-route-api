import bisect

# The algorithm (greedy, and exact for this problem)

# The state is where you are and how many miles of fuel are in the tank.

# At the start, you can only reach stations within 500 miles. Go to the cheapest of those. Whatever is left in the starting tank is already paid for.
# At each stop, look at the stations within 500 miles ahead:
# A cheaper one exists: buy only enough to reach the first cheaper one. Fuel is expensive here, so buy as little as possible.
# None is cheaper, but the destination is in range: buy only enough to arrive.
# None is cheaper and the destination is out of range: fill the tank, then drive to the cheapest station in range.
# Nothing is in range: the trip is impossible, so raise Infeasible.
class Infeasible(Exception):
    pass


def plan_fuel_stops(stations, total_miles, range_miles=500, mpg=10, start_fuel_miles=None):
    """
    stations: list of dicts with at least 'route_mile' and 'price' ($ per gallon).
    Returns (stops, total_cost). Each stop: {"station": dict, "gallons": float, "cost": float}.
    Only fuel BOUGHT on the trip is costed; the starting tank is assumed already paid for.
    """
    if start_fuel_miles is None:
        start_fuel_miles = range_miles          # leaves the start with a full tank

    stations = sorted(stations, key=lambda s: s["route_mile"])
    miles = [s["route_mile"] for s in stations]

    if total_miles <= start_fuel_miles:
        return [], 0.0                           # the starting tank is enough

    # Start: go to the cheapest station we can reach on the starting tank
    reachable = stations[: bisect.bisect_right(miles, start_fuel_miles)]
    if not reachable:
        raise Infeasible("No fuel station within range of the start location.")
    current = min(reachable, key=lambda s: (s["price"], -s["route_mile"]))
    fuel = start_fuel_miles - current["route_mile"]   # miles of fuel in the tank right now

    stops = []
    total_cost = 0.0

    while True:
        pos = current["route_mile"]
        lo = bisect.bisect_right(miles, pos)
        hi = bisect.bisect_right(miles, pos + range_miles)
        in_range = stations[lo:hi]                         # stations we could drive to on a full tank
        dest_reachable = total_miles - pos <= range_miles

        next_stop = next((s for s in in_range if s["price"] < current["price"]), None)

        going_to_dest = False
        fill_up = False
        if next_stop is None and dest_reachable:
            going_to_dest = True
            leg = total_miles - pos
        elif next_stop is None:
            if not in_range:
                raise Infeasible(f"No fuel station within {range_miles} miles after mile {pos:.0f}.")
            next_stop = min(in_range, key=lambda s: (s["price"], s["route_mile"]))
            fill_up = True
            leg = next_stop["route_mile"] - pos
        else:
            leg = next_stop["route_mile"] - pos

        buy = (range_miles - fuel) if fill_up else max(0.0, leg - fuel)   # miles of fuel to buy here
        if buy > 1e-9:
            gallons = buy / mpg
            cost = gallons * current["price"]
            total_cost += cost
            stops.append({"station": current, "gallons": gallons, "cost": cost})

        fuel += buy - leg                                  # buy, then drive the leg
        if going_to_dest:
            return stops, round(total_cost, 2)
        current = next_stop