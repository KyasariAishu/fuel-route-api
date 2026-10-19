# import csv
from django.core.management.base import BaseCommand
from routing.models import FuelStation
import pandas as pd 


def clean(value):
    # collapse repeated spaces, e.g. "I-35,  EXIT 271"
    return " ".join(str(value).split())

class Command(BaseCommand):
    help = "Load fuel prices from CSV"

    def add_arguments(self, parser):
        parser.add_argument("csv_path")

    def handle(self, *args, **options):
        df = pd.read_csv(options["csv_path"])
        # data=pd.read_csv('fuel-prices-for-be-assessment.csv',sep=',')
        rows_read = len(df)


        df = df.sort_values("Retail Price").drop_duplicates(
            subset="OPIS Truckstop ID", keep="first"
        )

        stations = []
        for row in df.to_dict("records"):
            print(row)
            rack = row["Rack ID"]
            stations.append(
                FuelStation(
                    opis_ID=int(row["OPIS Truckstop ID"]),
                    name=clean(row["Truckstop Name"]),
                    address=clean(row["Address"]),
                    city=clean(row["City"]),
                    state=clean(row["State"]),
                    rack_id=None if pd.isna(rack) else int(rack),
                    price=round(float(row["Retail Price"]), 3),
                )
            )
        FuelStation.objects.all().delete()  # makes re-running safe
        FuelStation.objects.bulk_create(stations, batch_size=500)
        self.stdout.write(
            self.style.SUCCESS(f"Read {rows_read} rows, saved {len(stations)} stations.")
        )
            
        #  run th command python manage.py load_fuel_prices fuel-prices-for-be-assessment.csv CLI