# Fuel Route API

Django API: give it a start and finish in the USA and it returns the driving route,
the cheapest places to fuel up (500-mile range, 10 mpg), and the total fuel cost.

## Setup
```
python -m venv ven
ven\Scripts\activate          # macOS/Linux: source ven/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py load_fuel_prices data/fuel-prices-for-be-assessment.csv
python manage.py geocode_stations    # fast: geocode_cache.json is committed
python manage.py runserver
copy .env.example .env      # then put your real email in .env (Nominatim requires it)
```


## Use
`GET /api/route/?start=Chicago, IL&finish=Dallas, TX`

or `POST /api/route/` with `{"start": "Chicago, IL", "finish": "Dallas, TX"}`.
Open the `map_url` field in a browser to see the route and fuel stops on a map.
`start`/`finish` also accept `lat,lon` (skips geocoding).

Errors: 400 missing input, 404 location not found, 422 trip not possible
(a stretch with no station within 500 miles), 502 routing service failed.

## How it works
1. Geocode start/finish (Nominatim, cached) and make ONE OSRM call for the route.
2. `cumulative_miles`: running distance along the route (haversine, scaled to OSRM's total).
3. `thin_route`: reduce ~9,000 points to about one per mile.
4. `stations_near_route`: a KD-tree over the route points finds each station's nearest
   point; stations within 5 miles are kept, and each gets a `route_mile`.
5. `plan_fuel_stops`: greedy algorithm. Go to the next cheaper station in range
   buying only what's needed; if none is cheaper, fill up and move to the cheapest
   station in range. Exact cost for a fixed route.

## Speed and API calls
- Per request: 1 routing call, plus up to 2 geocoding calls (0 for repeated places or lat,lon input).
- Identical requests are served from cache with no external calls.
- Stations are geocoded once ahead of time and held in memory as numpy arrays.

## Assumptions
- The vehicle starts with a full tank; only fuel bought on the trip is costed.
  A trip under 500 miles therefore costs $0.
- Station coordinates are city centres (the data has highway exits, not street addresses),
  so a station's position along the route is approximate.
- Duplicate OPIS IDs are reduced to the cheapest price. 26 Canadian locations were skipped.
- Fuel is bought at the station's listed price; detours of up to 5 miles are not costed.