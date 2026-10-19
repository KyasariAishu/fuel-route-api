import re

import requests
from django.conf import settings
from django.core.cache import cache 
from geopy.geocoders import Nominatim 
import hashlib
from geopy.exc import GeopyError

OSRM_URL = "https://router.project-osrm.org/route/v1/driving"
LATLON = re.compile(r"^\s*(-?\d+(\.\d+)?)\s*,\s*(-?\d+(\.\d+)?)\s*$")
# CHANGE THE EMAIL, same as before




class LocationNotFound(Exception):
    pass


class RoutingError(Exception):
    pass


def geocode(query):

    """Return (lat, lon). 'lat,lon' text skips the API call entirely."""
    # It calls the Nominatim API the first time for each place.
    m=LATLON.match(query)

    if m:
        return float(m.group(1)), float(m.group(3))

    key = key = "geo:" + hashlib.md5(query.lower().encode()).hexdigest()
    hit = cache.get(key)
    if hit:
        return hit

    geolocator = Nominatim(user_agent=settings.NOMINATIM_USER_AGENT, timeout=10)
    try:
        location = geolocator.geocode(query, country_codes="us")
    except GeopyError as e:
        raise RoutingError(f"Geocoding failed: {e}")
    if location is None:
        raise LocationNotFound(f"Could not find a US location for '{query}'")

    result = (location.latitude, location.longitude)
    # The result is then remembered in Django’s in-memory cache . cache disappears when the server restarts.
    cache.set(key, result, 24 * 3600)
    return result


def fetch_route(start, finish):
    """ONE OSRM call. start/finish are (lat, lon). Returns (coords, miles).
    coords is a list of [lon, lat] points along the road."""
    # OSRM wants lon,lat order, the opposite of what you have
    # OSRM has already chosen the one best road route.
    url = f"{OSRM_URL}/{start[1]},{start[0]};{finish[1]},{finish[0]}"
    try:
        r = requests.get(
            url,
            params={"overview": "full", "geometries": "geojson"},
            headers={"User-Agent": settings.NOMINATIM_USER_AGENT},
            timeout=15,
        )
        r.raise_for_status()
        route = r.json()["routes"][0]
    except (requests.RequestException, KeyError, IndexError, ValueError) as e:
        raise RoutingError(f"Routing failed: {e}")

    miles = route["distance"] / 1609.344   # OSRM returns meters
    return route["geometry"]["coordinates"], miles
