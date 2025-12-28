from django.core.management.base import BaseCommand
from django.utils import timezone

from byabulimi.weather_scraper import WeatherScraper, expires_in_hours
from byabulimi.models import LocalMarket, WeatherCache


class Command(BaseCommand):
    help = "Fetch weather for all LocalMarket locations and cache results."

    def add_arguments(self, parser):
        parser.add_argument("--source", choices=["open-meteo", "nasa"], default="open-meteo")
        parser.add_argument("--expiry-hours", type=int, default=6)

    def handle(self, *args, **options):
        source = options["source"]
        expiry = options["expiry_hours"]

        markets = LocalMarket.objects.all()
        if not markets.exists():
            self.stdout.write(self.style.WARNING("No LocalMarket entries found. Add markets before scraping."))
            return

        self.stdout.write(f"Fetching weather for {markets.count()} markets using {source}...")

        for m in markets:
            data = None
            if source == "open-meteo":
                data = WeatherScraper.fetch_open_meteo(m.latitude, m.longitude)
            elif source == "nasa":
                data = WeatherScraper.fetch_nasa_power(m.latitude, m.longitude)

            if data is None:
                self.stdout.write(self.style.ERROR(f"Failed for market {m} ({m.latitude},{m.longitude})"))
                continue

            expires_at = timezone.now() + timezone.timedelta(hours=expiry)

            WeatherCache.objects.create(
                market=m,
                district_name=m.district,
                source=source,
                data=data,
                expires_at=expires_at,
            )

            self.stdout.write(self.style.SUCCESS(f"Cached weather for {m} (expires {expires_at})"))

        self.stdout.write(self.style.NOTICE("Done."))
