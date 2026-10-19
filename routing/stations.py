from .geo import to_xyz
from .models import FuelStation

_cache = None


def get_stations():
    # Load stations once per server process and keep them in memory.
    # It keeps two things in memory: rows (name, city, price, and so on) and xyz (every station’s lat/lon converted to 3D sphere coordinates).
    global _cache
    if _cache is None:
        rows = list(
            FuelStation.objects.filter(lat__isnull=False, lon__isnull=False)
            .values("opis_ID", "name", "address", "city", "state", "price", "lat", "lon")
        )
        for r in rows:
            r["price"] = float(r["price"])
            r["lat"] = float(r["lat"])
            r["lon"] = float(r["lon"])
        xyz = to_xyz([r["lat"] for r in rows], [r["lon"] for r in rows])
        _cache = {"rows": rows, "xyz": xyz}
    return _cache