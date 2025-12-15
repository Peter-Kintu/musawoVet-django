# byabulimi/serializers.py (Updated)

from rest_framework import serializers
from .models import Farmer, Query, Advice

# 1. Farmer Serializers (Unchanged)
class FarmerRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Farmer
        fields = ['phone_number', 'language_code', 'region']

class FarmerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Farmer
        fields = ['phone_number', 'language_code', 'region', 'is_premium', 'date_joined']

# 2. Advice Serializer (Unchanged)
class AdviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advice
        fields = ['diagnosis_code', 'confidence_score', 'localized_advice', 'is_expert_referred']

# 3. Query Serializer for History (Unchanged)
class QueryHistorySerializer(serializers.ModelSerializer):
    advice = AdviceSerializer(read_only=True) # Nested advice object

    class Meta:
        model = Query
        fields = ['id', 'timestamp', 'raw_query_text', 'detected_crop', 'image', 'advice']

# 4. Query Submission Serializer (Updated for JSON Base64 submission)
class QuerySubmitSerializer(serializers.Serializer):
    # These fields are what the Flutter app sends in the JSON body
    image_base64 = serializers.CharField() 
    query_text = serializers.CharField(max_length=500, required=False)
    detected_crop = serializers.CharField(max_length=50)
    local_id = serializers.IntegerField() # Flutter's local ID for tracking