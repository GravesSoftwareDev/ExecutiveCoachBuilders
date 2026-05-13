import shutil
from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.management.base import BaseCommand

from garage.models import Vehicle


def find_static_image(relative_path):
    """
    Locate a static image file in both dev (finders) and production (STATIC_ROOT).
    Returns a Path if found, otherwise None.
    """
    # Works in development (DEBUG=True)
    result = finders.find(relative_path)
    if result:
        return Path(result)
    # Works in production — collectstatic puts files here
    candidate = Path(settings.STATIC_ROOT) / relative_path
    if candidate.exists():
        return candidate
    return None

VEHICLES = [
    # name, slug, category, passenger_capacity, image filename, display_order, used_vehicle
    ("Chevy EC33 Limo Bus - 25 Passenger",          "chevy-ec33-limo-bus-25-passenger",                "limo",       "25",    "CHEVY EC33 LIMO BUS 25 PASSENGER.jpg",          1,  False),
    ("Chevy EC33 Shuttle - 27 Passenger",            "chevy-ec33-shuttle-27-passenger",                 "shuttle",    "27",    "CHEVY EC33 SHUTTLE 27 PASSENGR.jpg",            2,  False),
    ("Chevy EC38 Limo Bus - 34 Passenger",           "chevy-ec38-limo-bus-34-passenger",                "limo",       "34",    "CHEVY EC38 LIMO BUS 34 PASSENGER.jpg",          3,  False),
    ("Chevy EC38 Shuttle - 35 Passenger",            "chevy-ec38-shuttle-35-passenger",                 "shuttle",    "35",    "CHEVY EC38 SHUTTLE 35 PASSENGER.jpg",           4,  False),
    ("Mega 45 - 51 Passenger",                       "mega-45-51-passenger",                            "motorcoach", "45–51", "MEGA 45 51 PASSENGER.jpg",                      5,  False),
    ("Mercedes Sprinter Custom",                     "mercedes-sprinter-custom",                        "sprinter",   "",      "MERCEDES SPRINTER CUSTOM.jpg",                  6,  False),
    ("Mercedes Sprinter Diplomat - 10 Passenger",    "mercedes-sprinter-diplomat-10-passenger",         "sprinter",   "10",    "MERCEDES SPRINTER DIPLOMAT 10 PASSENGER.jpg",   7,  False),
    ("Mercedes Sprinter Golf - 11 Passenger",        "mercedes-sprinter-golf-11-passenger",             "sprinter",   "11",    "MERCEDES SPRINTER GOLF 11 PASSENGER.jpg",       8,  False),
    ("Mercedes Sprinter Limousine - 16 Passenger",   "mercedes-sprinter-limousine-16-passenger",        "limo",       "16",    "MERCEDES SPRINTER LIMOUSINE 16-PASSENGER .jfif", 9, False),
    ("Mercedes Sprinter Shuttle - 13 Passenger",     "mercedes-sprinter-shuttle-13-passenger",          "shuttle",    "13",    "MERCEDES SPRINTER SHUTTLE 13 PASSENGER .jfif",  10, False),
    ("SuperCoach XL - 57 Passenger",                 "supercoach-xl-57-passenger",                      "motorcoach", "57",    "SUPERCOACH XL 57 PASSENGER.jpg",                11, False),
    ("Widebody 45 - 51 Passenger",                   "widebody-45-51-passenger",                        "motorcoach", "45–51", "WIDEBODY 45 51- PASSENGER.jpg",                 12, False),
    # Used vehicle duplicates
    ("Chevy EC33 Limo Bus - 25 Passenger",           "used-chevy-ec33-limo-bus-25-passenger",           "limo",       "25",    "CHEVY EC33 LIMO BUS 25 PASSENGER.jpg",          1,  True),
    ("Chevy EC38 Limo Bus - 34 Passenger",           "used-chevy-ec38-limo-bus-34-passenger",           "limo",       "34",    "CHEVY EC38 LIMO BUS 34 PASSENGER.jpg",          2,  True),
    ("Mercedes Sprinter Diplomat - 10 Passenger",    "used-mercedes-sprinter-diplomat-10-passenger",    "sprinter",   "10",    "MERCEDES SPRINTER DIPLOMAT 10 PASSENGER.jpg",   3,  True),
    ("Widebody 45 - 51 Passenger",                   "used-widebody-45-51-passenger",                   "motorcoach", "45–51", "WIDEBODY 45 51- PASSENGER.jpg",                 4,  True),
]


class Command(BaseCommand):
    help = "Seed the database with demo vehicles and copy their images to media."

    def _copy_image(self, image_file, media_vehicles):
        src = find_static_image(f"images/{image_file}")
        if src:
            dst = media_vehicles / image_file
            if not dst.exists():
                shutil.copy2(src, dst)
            return f"vehicles/{image_file}"
        self.stderr.write(f"  Image not found: images/{image_file}")
        return None

    def _fix_images(self, media_vehicles):
        """Update existing vehicles that have empty hero_image paths."""
        media_vehicles.mkdir(parents=True, exist_ok=True)
        for name, slug, category, capacity, image_file, order, used in VEHICLES:
            try:
                vehicle = Vehicle.objects.get(slug=slug)
            except Vehicle.DoesNotExist:
                continue
            if not vehicle.hero_image:
                path = self._copy_image(image_file, media_vehicles)
                if path:
                    vehicle.hero_image = path
                    vehicle.save(update_fields=["hero_image"])
                    self.stdout.write(f"  Fixed image: {slug}")

    def handle(self, *args, **options):
        media_vehicles = Path(settings.MEDIA_ROOT) / "vehicles"
        media_vehicles.mkdir(parents=True, exist_ok=True)

        if Vehicle.objects.exists():
            self.stdout.write("Vehicles already exist — fixing any missing images.")
            self._fix_images(media_vehicles)
            return

        for name, slug, category, capacity, image_file, order, used in VEHICLES:
            hero_image_field = self._copy_image(image_file, media_vehicles) or ""

            Vehicle.objects.create(
                name=name,
                slug=slug,
                category=category,
                passenger_capacity=capacity,
                hero_image=hero_image_field,
                display_order=order,
                used_vehicle=used,
                is_published=True,
                tagline="",
                description="",
                features="",
            )
            prefix = "[used] " if used else ""
            self.stdout.write(f"  Created: {prefix}{name}")

        self.stdout.write(self.style.SUCCESS("Vehicle seed complete."))
