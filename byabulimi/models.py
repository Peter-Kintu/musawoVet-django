# byabulimi/models.py

from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

# Helper function to define where the images are stored
def query_image_upload_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/query_images/farmer_<id>/<filename>
    # Works because Query has a foreign key to Farmer
    return f'query_images/farmer_{instance.farmer.id}/{filename}'

# 1. Farmer Model (Extended User Profile)
class Farmer(models.Model):
    """
    EXTENDED PROFILE: This links a Django User account to a Farmer's specific data.
    The 'user' field is required for authentication and request.user.farmer access.
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='farmer',
        help_text="Link to the Django User account for authentication"
    )
    
    # We keep the phone_number as it's the primary identifier in the UI
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
    
    # Store the image file
    image = models.ImageField(upload_to=query_image_upload_path, blank=True, null=True) 
    
    # The transcribed voice or text input
    raw_query_text = models.TextField(blank=True, null=True)
    
    # The crop or animal being diagnosed
    detected_crop = models.CharField(max_length=50, default='Unknown')

    def __str__(self):
        return f"Query {self.id} by {self.farmer.phone_number} on {self.detected_crop}"

# 3. Advice Model (Gemini's Response and Metadata)
class Advice(models.Model):
    # OneToOneField ensures each Query has exactly one Advice response
    query = models.OneToOneField(Query, on_delete=models.CASCADE, primary_key=True)
    
    diagnosis_code = models.CharField(max_length=50, blank=True, null=True)
    confidence_score = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('0.00')) # 0.00 to 1.00
    localized_advice = models.TextField(help_text="The final, localized treatment/prevention text.")
    is_expert_referred = models.BooleanField(default=False)
    
    # Essential for debugging and audit trail
    gemini_prompt = models.TextField(blank=True, null=True) 

    def __str__(self):
        return f"Advice for Query {self.query.id}: {self.diagnosis_code}"
