import numpy as np

from scipy.spatial import cKDTree

EARTH_RADIUS_MILES = 3958.8


def to_xyz(lat, lon):
    # Degrees -> points on a unit sphere, so straight-line distance is valid.
    lat = np.radians(np.asarray(lat, dtype=float))
    lon = np.radians(np.asarray(lon, dtype=float))
    return np.column_stack([
        np.cos(lat) * np.cos(lon),
        np.cos(lat) * np.sin(lon),
        np.sin(lat),
    ])


def cumulative_miles(coords, total_miles):
    # coords: list of [lon, lat] from OSRM.

    # Returns an array: miles from the start at every point (first = 0, last = total_miles).

#     segments (haversine):  A→B = 0.4   B→C = 0.3   C→D = 0.5
# running total:         [0, 0.4, 0.7, 1.2]
    pts = np.asarray(coords, dtype=float)
    # print("Points from cumulative "+str(pts))
    lat = np.radians(pts[:, 1])
    lon = np.radians(pts[:, 0])

    # using Haversine formula to find distance between two corrdinates and find total miles
    dlat = np.diff(lat)
    dlon = np.diff(lon)
    a = np.sin(dlat / 2) ** 2 + np.cos(lat[:-1]) * np.cos(lat[1:]) * np.sin(dlon / 2) ** 2
    segment_miles = 2 * EARTH_RADIUS_MILES * np.arcsin(np.sqrt(a))
    cum = np.concatenate([[0.0], np.cumsum(segment_miles)])
    return cum * (total_miles / cum[-1])


def thin_route(coords, cum, step_miles=1.0):
    # Keep roughly one point per mile. Returns (points as [lon, lat] array, their cumulative miles).
    pts = np.asarray(coords, dtype=float)
    marks = np.arange(0, cum[-1], step_miles)         # 0, 1, 2, ... miles
    idx = np.searchsorted(cum, marks)                  # first point at or past each mark
    idx = np.unique(np.append(idx, len(cum) - 1))      # dedupe and always keep the last point
    return pts[idx], cum[idx]

def stations_near_route(route_pts, route_cum, station_xyz, radius_miles=5.0):
    # For every station: nearest route point, and how far away it is.
    # Returns (station_indices, route_miles, off_route_miles) for stations within the radius.

    # It answers “which stations are near the road, and how far along it is each one?”
    route_xyz = to_xyz(route_pts[:, 1], route_pts[:, 0])   #  [:,1] is lat & [:,0] is lon
    tree = cKDTree(route_xyz)

    dist, nearest = tree.query(station_xyz)                # one vectorised call for all stations
    off_route = dist * EARTH_RADIUS_MILES                  # unit-sphere distance -> miles
    keep = off_route <= radius_miles

    return np.nonzero(keep)[0], route_cum[nearest[keep]], off_route[keep]



