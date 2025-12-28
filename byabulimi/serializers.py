import re
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Farmer, Query, Advice

# --- 1. Farmer Serializers ---

class FarmerRegisterSerializer(serializers.ModelSerializer):
    """
    Handles dual-creation of a Django User and a Farmer profile.
    Includes normalization to ensure login credentials match.
    """
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    full_name = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Farmer
        # fields list matches what the Flutter ApiService sends
        fields = ['phone_number', 'password', 'full_name', 'language_code', 'region']

    def validate_phone_number(self, value):
        """Check if a user with this normalized phone already exists."""
        clean_phone = re.sub(r'[^\d+]', '', value)
        if User.objects.filter(username=clean_phone).exists():
            raise serializers.ValidationError("A farmer with this phone number is already registered.")
        return value

    def create(self, validated_data):
        # 1. Extract data
        password = validated_data.pop('password')
        full_name = validated_data.pop('full_name', '')
        raw_phone = validated_data.get('phone_number')

        # 2. NORMALIZE PHONE NUMBER
        # This MUST match the _normalizePhone logic in your Flutter ApiService.
        clean_phone = re.sub(r'[^\d+]', '', raw_phone)

        # 3. Create the ACTUAL Django User
        # We use the cleaned phone number as the 'username' for Token Auth compatibility
        user = User.objects.create_user(
            username=clean_phone,
            password=password,
            first_name=full_name
        )

        # 4. Create the Farmer profile linked to that User
        validated_data['phone_number'] = clean_phone
        farmer = Farmer.objects.create(user=user, **validated_data)
        
        return farmer

class FarmerProfileSerializer(serializers.ModelSerializer):
    # Pull the name from the linked User account
    full_name = serializers.CharField(source='user.first_name', read_only=True)

    class Meta:
        model = Farmer
        fields = ['phone_number', 'full_name', 'language_code', 'region', 'is_premium', 'date_joined']


# --- 2. Advice Serializer ---

class AdviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advice
        fields = [
            'diagnosis_code', 
            'confidence_score', 
            'localized_advice', 
            'english_summary', 
            'is_expert_referred'
        ]


# --- 3. Query Serializer for History ---

class QueryHistorySerializer(serializers.ModelSerializer):
    """
    Serializes historical queries including the AI Advice.
    Note: 'advice' is the reverse relation from the OneToOneField.
    """
    advice = AdviceSerializer(read_only=True)

    class Meta:
        model = Query
        fields = ['id', 'timestamp', 'raw_query_text', 'detected_crop', 'image', 'advice']


# --- 4. Query Submission Serializer ---

class QuerySubmitSerializer(serializers.Serializer):
    """
    Handles the multimodal JSON payload from the Flutter app.
    Matches the 'QueryRequest' class in the Flutter models.
    """
    local_id = serializers.IntegerField()
    farmer_id = serializers.CharField()
    detected_crop = serializers.CharField(max_length=50)
    query_text = serializers.CharField(max_length=500, required=False, allow_blank=True)
    image_base64 = serializers.CharField()