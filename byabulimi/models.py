# byabulimi/models.py

from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator

# Helper function to define where the images are stored
def query_image_upload_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/query_images/farmer_<id>/<filename>
    return f'query_images/farmer_{instance.farmer.id}/{filename}'

# 1. Farmer Model (Extended User Profile)
class Farmer(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='farmer',
        help_text="Link to the Django User account for authentication"
    )
    phone_number = models.CharField(max_length=15, unique=True)
    language_code = models.CharField(max_length=5, default='lug', help_text="Preferred language (e.g., 'lug', 'swa')")
    region = models.CharField(max_length=100, blank=True, null=True, help_text="Used for localized weather/market alerts")
    is_premium = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Farmer: {self.phone_number} ({self.user.username})"

# 2. Query Model (The Farmer's Request)
class Query(models.Model):
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, related_name='queries')
    timestamp = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to=query_image_upload_path, blank=True, null=True) 
    raw_query_text = models.TextField(blank=True, null=True)
    detected_crop = models.CharField(max_length=50, default='Unknown')

    def __str__(self):
        return f"Query {self.id} by {self.farmer.phone_number} on {self.detected_crop}"

# 3. Advice Model (Gemini's Response and Metadata)
class Advice(models.Model):
    query = models.OneToOneField(Query, on_delete=models.CASCADE, primary_key=True)
    diagnosis_code = models.CharField(max_length=50, blank=True, null=True)
    confidence_score = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('0.00'))
    localized_advice = models.TextField(help_text="The final, localized treatment/prevention text.")
    is_expert_referred = models.BooleanField(default=False)
    gemini_prompt = models.TextField(blank=True, null=True) 

    def __str__(self):
        return f"Advice for Query {self.query.id}: {self.diagnosis_code}"

# --- NEW MODELS FOR NO-API WEATHER & MARKET SYSTEM ---


# 4. District Weather Model (Replaces OpenWeatherMap)
class DistrictWeather(models.Model):
    """Stores historical seasonal averages and current-season notes for districts.

    Notes:
    - `avg_monthly` stores optional per-month aggregates (JSON with keys like 'jan', 'feb').
    - Keep `avg_temp_c` and `avg_humidity` for quick access and filtering.
    """
    district_name = models.CharField(max_length=100, unique=True)
    avg_temp_c = models.FloatField(
        help_text="Average temperature in Celsius",
        validators=[MinValueValidator(-50.0), MaxValueValidator(60.0)],
    )
    avg_humidity = models.FloatField(
        help_text="Average percentage humidity",
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
    )
    avg_monthly = models.JSONField(blank=True, null=True, help_text="Optional JSON of monthly averages")
    current_season = models.CharField(max_length=50, help_text="e.g., First Rains, Dry Season")
    pest_warning = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "District Weather Data"
        ordering = ["district_name"]
        indexes = [models.Index(fields=["district_name"]) ]

    def __str__(self):
        return self.district_name


# 5. Local Market Model
class LocalMarket(models.Model):
    """Actual market locations used for price collection and lookup."""
    name = models.CharField(max_length=100)
    district = models.CharField(max_length=100, db_index=True)
    latitude = models.FloatField(validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)])
    longitude = models.FloatField(validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)])

    class Meta:
        unique_together = ("name", "district")
        ordering = ["district", "name"]

    def __str__(self):
        return f"{self.name} ({self.district})"


# 6. Commodity Price Model (Replaces external Market APIs)
class CommodityPrice(models.Model):
    """Price records for commodities at a given `LocalMarket`.

    Uniqueness: `market` + `product_name` + `unit` prevents duplicate simultaneous entries.
    """
    CATEGORY_CROP = 'crop'
    CATEGORY_LIVESTOCK = 'livestock'
    CATEGORY_CHOICES = [
        (CATEGORY_CROP, 'Crop'),
        (CATEGORY_LIVESTOCK, 'Livestock'),
    ]

    TREND_UP = 'up'
    TREND_DOWN = 'down'
    TREND_STABLE = 'stable'
    TREND_CHOICES = [
        (TREND_UP, 'Up'),
        (TREND_DOWN, 'Down'),
        (TREND_STABLE, 'Stable'),
    ]

    market = models.ForeignKey(LocalMarket, on_delete=models.CASCADE, related_name='prices')
    product_name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    unit = models.CharField(max_length=20, default="kg")
    trend = models.CharField(max_length=10, choices=TREND_CHOICES, default=TREND_STABLE)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("market", "product_name", "unit")
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.product_name} at {self.market.name} ({self.price} {self.unit})"


# 7. Weather Cache & Crowdsourced Reports
class WeatherCache(models.Model):
    """Cached raw weather data fetched by scrapers/fetchers to avoid repeated external calls.

    - `market` is optional; when present the cache is tied to a specific market location.
    - `district_name` can be used when data is at a district level.
    """
    market = models.ForeignKey(LocalMarket, on_delete=models.CASCADE, related_name='weather', blank=True, null=True)
    district_name = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    source = models.CharField(max_length=50, help_text="e.g., open-meteo, nasa-power, unma-scrape")
    data = models.JSONField()
    fetched_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True, help_text="When this cache entry should be considered stale")

    class Meta:
        ordering = ["-fetched_at"]

    def __str__(self):
        target = self.market.name if self.market else (self.district_name or "unknown")
        return f"WeatherCache({target}, {self.source}, {self.fetched_at.isoformat()})"


class CrowdsourcedReport(models.Model):
    """Farmer-submitted local observations used to augment automated sources.

    Example workflow: when several reports of the same type exist for a district within
    a short window, the backend can promote that as a local event.
    """
    REPORT_RAIN = 'rain'
    REPORT_DRY = 'dry'
    REPORT_STORM = 'storm'
    REPORT_CHOICES = [
        (REPORT_RAIN, 'Heavy Rain'),
        (REPORT_DRY, 'Dry / No Rain'),
        (REPORT_STORM, 'Storm / Wind Damage'),
    ]

    farmer = models.ForeignKey('Farmer', on_delete=models.SET_NULL, null=True, blank=True)
    district = models.CharField(max_length=100, db_index=True)
    report_type = models.CharField(max_length=20, choices=REPORT_CHOICES)
    detail = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.district}: {self.get_report_type_display()} @ {self.created_at.isoformat()}"