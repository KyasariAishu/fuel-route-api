import json
from urllib.parse import urlencode

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .planner import Infeasible
from .services import LocationNotFound, RoutingError
from .trip import build_plan

MAP_HTML = """<!doctype html><html><head><meta charset="utf-8"><title>Fuel route</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<style>html,body,#map{height:100%;margin:0}
#box{position:absolute;z-index:1000;top:10px;right:10px;background:#fff;padding:10px 14px;
font:14px system-ui;border-radius:8px;box-shadow:0 1px 6px #0004}</style></head>
<body><div id="map"></div><div id="box"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const d = __DATA__;
const map = L.map('map');
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{
  attribution:'&copy; OpenStreetMap contributors',
  referrerPolicy:'strict-origin-when-cross-origin'
}).addTo(map);
const line = L.geoJSON(d.route,{style:{color:'#2563eb',weight:5}}).addTo(map);
map.fitBounds(line.getBounds());
L.marker([d.start.lat,d.start.lon]).addTo(map).bindPopup('Start: '+d.start.query);
L.marker([d.finish.lat,d.finish.lon]).addTo(map).bindPopup('Finish: '+d.finish.query);
d.fuel_stops.forEach((s,i)=>L.circleMarker([s.lat,s.lon],{radius:9,color:'#dc2626',fillOpacity:.9}).addTo(map)
 .bindPopup(`<b>Stop ${i+1}: ${s.name}</b><br>${s.city}, ${s.state}<br>$${s.price_per_gallon}/gal<br>${s.gallons_purchased} gal = $${s.cost}`));
document.getElementById('box').innerHTML =
 `<b>${d.distance_miles} mi</b><br>${d.fuel_stops.length} fuel stop(s)<br>Total fuel: <b>$${d.total_fuel_cost}</b>`;
</script></body></html>"""


def _params(request):
    if request.method == "POST":
        try:
            return json.loads(request.body or b"{}")
        except ValueError:
            return {}
    return request.GET


@csrf_exempt
@require_http_methods(["GET", "POST"])
def route_plan(request):
    data = _params(request)
    start = str(data.get("start") or "").strip()
    finish = str(data.get("finish") or "").strip()
    if not start or not finish:
        return JsonResponse(
            {"error": "Both 'start' and 'finish' are required (e.g. 'Chicago, IL')."}, status=400
        )

    try:
        result = build_plan(start, finish)
    except LocationNotFound as e:
        return JsonResponse({"error": str(e)}, status=404)
    except Infeasible as e:
        return JsonResponse({"error": str(e)}, status=422)
    except RoutingError as e:
        return JsonResponse({"error": str(e)}, status=502)

    if request.GET.get("format") == "html":
        payload = json.dumps(result).replace("</", "<\\/")
        return HttpResponse(MAP_HTML.replace("__DATA__", payload))

    qs = urlencode({"start": start, "finish": finish, "format": "html"})
    return JsonResponse({**result, "map_url": request.build_absolute_uri(f"{request.path}?{qs}")})