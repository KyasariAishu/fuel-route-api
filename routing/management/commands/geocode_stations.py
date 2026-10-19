import json 
from pathlib import Path
from django.core.management.base import BaseCommand
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
from django.conf import settings

from routing.models import FuelStation

CACHE_FILE = Path(settings.BASE_DIR) / "geocode_cache.json"

def make_key(city, state):
    return f"{city}|{state}".lower()

class Command(BaseCommand):
    help = "Geocode each unique city/state once and store lat/lon on the stations"
    def handle(self, *args, **options):
        geolocator = Nominatim(user_agent=settings.NOMINATIM_USER_AGENT)
        geocode = RateLimiter(
            geolocator.geocode,
            min_delay_seconds=1.1,   # Nominatim allows 1 request/second
            max_retries=2,
            error_wait_seconds=5,
            swallow_exceptions=True,  # a failure returns None instead of crashing
        )

        cache = json.loads(CACHE_FILE.read_text()) if CACHE_FILE.exists() else {}


        pairs = sorted(set(FuelStation.objects.values_list("city", "state")))
        todo = [p for p in pairs if make_key(*p) not in cache]
        self.stdout.write(f"{len(pairs)} unique places, {len(todo)} still to geocode")


        missing = []
        for i, (city, state) in enumerate(todo, 1):
            location = geocode(f"{city}, {state}", country_codes="us")
            if location is None:
                missing.append((city, state))   # not cached, so a rerun retries it
            else:
                cache[make_key(city, state)] = [location.latitude, location.longitude]
                print(cache[make_key(city,state)])
                CACHE_FILE.write_text(json.dumps(cache))
            if i % 25 == 0:
                self.stdout.write(f"{i}/{len(todo)} done")


        stations = list(FuelStation.objects.all())
        with_coords = 0
        for s in stations:
            coords = cache.get(make_key(s.city, s.state))
            if coords:
                lat, lon = coords
                if 24 <= lat <= 50 and -125 <= lon <= -66:   # rough USA box
                    s.lat, s.lon = lat, lon
                    with_coords += 1
                else:
                    self.stdout.write(f"Suspicious match: {s.city}, {s.state} -> {coords}")
        FuelStation.objects.bulk_update(stations, ["lat", "lon"], batch_size=500)


        self.stdout.write(self.style.SUCCESS(
            f"{with_coords}/{len(stations)} stations have coordinates; "
            f"{len(missing)} places not found: {missing[:10]}"
        ))


        