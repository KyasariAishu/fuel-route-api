from django.test import TestCase

# Create your tests here.
import unittest

from routing.planner import Infeasible, plan_fuel_stops

from unittest.mock import patch

import numpy as np
from django.test import SimpleTestCase

from routing.geo import cumulative_miles, thin_route
from routing.services import LocationNotFound



class GeoTests(unittest.TestCase):
    def test_cumulative_miles_starts_at_zero_ends_at_total(self):
        coords = [[0, 0], [0.1, 0], [0.2, 0]]
        cum = cumulative_miles(coords, 13.8)
        self.assertEqual(cum[0], 0)
        self.assertAlmostEqual(cum[-1], 13.8)
        self.assertTrue(np.all(np.diff(cum) > 0))

    def test_thin_route_keeps_first_and_last_and_dedupes(self):
        cum = np.array([0, 0.15, 0.3, 1.3, 3.1, 6.0])
        coords = [[i, i] for i in range(6)]
        _, kept = thin_route(coords, cum, step_miles=1.0)
        self.assertEqual(list(kept), [0, 1.3, 3.1, 6.0])


class ApiTests(SimpleTestCase):
    def test_missing_finish_is_400(self):
        r = self.client.get("/api/route/", {"start": "Chicago, IL"})
        self.assertEqual(r.status_code, 400)

    @patch("routing.views.build_plan", side_effect=LocationNotFound("nope"))
    def test_unknown_place_is_404(self, _):
        r = self.client.get("/api/route/", {"start": "x", "finish": "y"})
        self.assertEqual(r.status_code, 404)

    @patch("routing.views.build_plan", side_effect=Infeasible("gap"))
    def test_infeasible_is_422(self, _):
        r = self.client.get("/api/route/", {"start": "x", "finish": "y"})
        self.assertEqual(r.status_code, 422)
        

def s(mile, price):
    return {"route_mile": mile, "price": price}


class PlannerTests(unittest.TestCase):
    def test_short_trip_needs_no_stop(self):
        self.assertEqual(plan_fuel_stops([s(100, 3.0)], 400), ([], 0.0))

    def test_example_from_the_walkthrough(self):
        stops, cost = plan_fuel_stops([s(300, 5.0), s(450, 3.0), s(900, 4.0)], 1000)
        self.assertEqual([x["station"]["route_mile"] for x in stops], [450, 900])
        self.assertAlmostEqual(stops[0]["gallons"], 45)
        self.assertAlmostEqual(stops[1]["gallons"], 5)
        self.assertAlmostEqual(cost, 155.0)

    def test_no_stations(self):
        with self.assertRaises(Infeasible):
            plan_fuel_stops([], 1000)

    def test_gap_too_big(self):
        with self.assertRaises(Infeasible):
            plan_fuel_stops([s(100, 3.0)], 1500)




if __name__ == "__main__":
    unittest.main()