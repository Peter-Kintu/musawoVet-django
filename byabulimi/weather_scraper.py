import logging
from datetime import datetime, timedelta
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class WeatherScraper:
    """Flexible fetcher supporting Open-Meteo, NASA POWER and site scraping.

    Implementations:
    - `fetch_open_meteo(lat, lon)` — no API key, simple JSON.
    - `fetch_nasa_power(lat, lon)` — useful agricultural variables (example skeleton).
    - `scrape_unma(url, parser)` — minimal BeautifulSoup-based skeleton (parser must be provided).
    """

    OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
    NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

    @staticmethod
    def fetch_open_meteo(lat: float, lon: float, timezone: str = "UTC") -> Optional[dict]:
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "timezone": timezone,
        }
        try:
            resp = requests.get(WeatherScraper.OPEN_METEO_URL, params=params, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.exception("Open-Meteo fetch failed: %s", e)
            return None

    @staticmethod
    def fetch_nasa_power(lat: float, lon: float, start: str = None, end: str = None) -> Optional[dict]:
        # NASA POWER expects dates like YYYYMMDD; provide defaults for last 7 days
        if not end:
            end = datetime.utcnow().strftime("%Y%m%d")
        if not start:
            start = (datetime.utcnow() - timedelta(days=7)).strftime("%Y%m%d")
        params = {
            "start": start,
            "end": end,
            "units": "metric",
            "latitude": lat,
            "longitude": lon,
            "parameters": "PRECTOT,T2M_MAX,T2M_MIN,WS2M",
            "format": "JSON",
        }
        try:
            resp = requests.get(WeatherScraper.NASA_POWER_URL, params=params, timeout=20)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.exception("NASA POWER fetch failed: %s", e)
            return None

    @staticmethod
    def scrape_unma(url: str, parser_callable):
        """Generic scraper for UNMA or other bulletin pages.

        `parser_callable` should accept a BeautifulSoup object and return a dict-like payload.
        This is intentionally generic because website structures change; implement specific
        parsers in your project when you inspect the page HTML.
        """
        from bs4 import BeautifulSoup

        try:
            resp = requests.get(url, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            return parser_callable(soup)
        except Exception as e:
            logger.exception("Error scraping %s: %s", url, e)
            return None


def expires_in_hours(hours: int = 6):
    return datetime.utcnow() + timedelta(hours=hours)
