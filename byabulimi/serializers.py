# byabulimi/serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Farmer, Query, Advice

# --- 1. Farmer Serializers ---

class FarmerRegisterSerializer(serializers.ModelSerializer):
    """
    Updated to handle dual-creation of a Django User and a Farmer profile.
    This ensures that passwords are encrypted and login works.
    """
    # These fields are sent by Flutter but aren't in the Farmer model directly
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    full_name = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Farmer
        # fields list must match what the Flutter ApiService sends
        fields = ['phone_number', 'password', 'full_name', 'language_code', 'region']

    def create(self, validated_data):
        # 1. Extract data for the User account
        password = validated_data.pop('password')
        full_name = validated_data.pop('full_name', '')
        phone = validated_data.get('phone_number')

        # 2. Create the ACTUAL Django User (This makes login work)
        # We use the phone number as the 'username' for the token auth system
        user = User.objects.create_user(
            username=phone,
            password=password,
            first_name=full_name
        )

        # 3. Create the Farmer profile linked to that User
        # NOTE: Ensure your Farmer model in models.py has a OneToOneField to User
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
        fields = ['diagnosis_code', 'confidence_score', 'localized_advice', 'is_expert_referred']


# --- 3. Query Serializer for History ---

class QueryHistorySerializer(serializers.ModelSerializer):
    advice = AdviceSerializer(read_only=True) # Nested advice object

    class Meta:
        model = Query
        fields = ['id', 'timestamp', 'raw_query_text', 'detected_crop', 'image', 'advice']


# --- 4. Query Submission Serializer ---

class QuerySubmitSerializer(serializers.Serializer):
    """
    Handles the multimodal JSON payload from the Flutter app.
    """
    image_base64 = serializers.CharField() 
    query_text = serializers.CharField(max_length=500, required=False, allow_blank=True)
    detected_crop = serializers.CharField(max_length=50)
    local_id = serializers.IntegerField() # Flutter's local ID for tracking sync status
