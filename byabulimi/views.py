# byabulimi/views.py (Updated with Gemini Integration)

import base64
from decimal import Decimal
from django.core.files.base import ContentFile
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Farmer, Query, Advice
from .serializers import (
    FarmerRegisterSerializer, FarmerProfileSerializer, 
    QuerySubmitSerializer, QueryHistorySerializer
)
# Import the Gemini function and the file helper
from .ai_service import generate_diagnosis, file_to_part 

# --- 1. Authentication & Profile Views (Unchanged) ---

class FarmerRegisterAPIView(generics.CreateAPIView):
    """API view to register a new farmer."""
    queryset = Farmer.objects.all()
    serializer_class = FarmerRegisterSerializer
    permission_classes = [permissions.AllowAny]

class FarmerProfileAPIView(generics.RetrieveAPIView):
    """API view to retrieve the profile of the authenticated farmer."""
    serializer_class = FarmerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        try:
            return self.request.user.farmer
        except Farmer.DoesNotExist:
            return None

# --- 2. Core Diagnostic Query Views (UPDATED) ---

class QuerySubmitAPIView(generics.CreateAPIView):
    """API view to receive the multimodal query and trigger Gemini diagnosis."""
    serializer_class = QuerySubmitSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def _create_advice(self, query: Query, diagnosis_output: dict):
        """Helper to create and save the Advice object."""
        
        advice_instance = Advice.objects.create(
            query=query,
            diagnosis_code=diagnosis_output.get("diagnosis_code"),
            # Convert float from Gemini output to Decimal for the Django model
            confidence_score=Decimal(str(diagnosis_output.get("confidence_score", 0.0))),
            # The key is 'localized_advice_luganda' from ai_config, mapped to 'localized_advice' in models
            localized_advice=diagnosis_output.get("localized_advice_luganda", diagnosis_output.get("english_summary", "No advice returned.")),
            is_expert_referred=diagnosis_output.get("is_expert_referral_needed", False),
            gemini_prompt=f"Query: {query.raw_query_text}, Crop: {query.detected_crop}"
        )
        return advice_instance

    def post(self, request, *args, **kwargs):
        # The request data is expected to be JSON
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 1. Get validated data
        base64_data = serializer.validated_data.get('image_base64')
        query_text = serializer.validated_data.get('query_text')
        detected_crop = serializer.validated_data.get('detected_crop')
        farmer = self.request.user.farmer
        # local_id = serializer.validated_data.get('local_id')

        # 2. Decode Base64 image and prepare Django ContentFile
        try:
            # Decode the base64 string into raw bytes
            image_bytes = base64.b64decode(base64_data)
            # Create a ContentFile for Django's ImageField
            image_file = ContentFile(image_bytes, name=f'{farmer.phone_number}_{detected_crop}_query.jpg')
        except Exception as e:
            return Response({"message": f"Invalid image format: {e}"}, status=status.HTTP_400_BAD_REQUEST)


        # 3. Save the raw query locally (before the AI call)
        new_query = Query.objects.create(
            farmer=farmer,
            image=image_file,
            raw_query_text=query_text,
            detected_crop=detected_crop,
        )
        
        # 4. Prepare for and call the AI service
        image_part = file_to_part(image_bytes)
        
        diagnosis_output = generate_diagnosis(
            image_part=image_part, 
            query_text=query_text, 
            detected_crop=detected_crop, 
            language_code=farmer.language_code
        )
        
        # 5. Create and save the Advice object from the Gemini output
        advice_instance = self._create_advice(new_query, diagnosis_output)

        # 6. Return the final structured response to the Flutter app (synchronous)
        # Matches the expected Flutter DiagnosisResponse structure
        return Response({
            "query_id": new_query.id,
            "message": "Diagnosis complete.",
            "localized_advice": advice_instance.localized_advice,
            "english_summary": diagnosis_output.get("english_summary"),
            "confidence_score": float(advice_instance.confidence_score), # Convert Decimal back to float
            "is_expert_referred": advice_instance.is_expert_referred,
            "diagnosis_code": advice_instance.diagnosis_code,
        }, status=status.HTTP_201_CREATED) 

class QueryHistoryAPIView(generics.ListAPIView):
    """API view to retrieve the authenticated farmer's query history."""
    serializer_class = QueryHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Query.objects.filter(farmer=self.request.user.farmer).order_by('-timestamp')

# --- 3. Market & Weather Data Views (Stubs - Unchanged) ---

class WeatherAlertsAPIView(generics.RetrieveAPIView):
    """Stub for retrieving regional weather/pest data."""
    permission_classes = [permissions.IsAuthenticated]
    
    def retrieve(self, request, *args, **kwargs):
        # Logic to pull cached data for request.user.farmer.region
        return Response({
            "region": request.user.farmer.region,
            "forecast_7_day": "Sunny with isolated thunderstorms.",
            "pest_risk": "Moderate risk of Fall Armyworm in maize fields.",
        })

class MarketPricesAPIView(generics.RetrieveAPIView):
    """Stub for retrieving local market prices."""
    permission_classes = [permissions.IsAuthenticated]
    
    def retrieve(self, request, *args, **kwargs):
        # Logic to pull cached price data for request.user.farmer.region
        return Response({
            "region": request.user.farmer.region,
            "prices": [
                {"crop": "Maize", "price": 1200, "unit": "UGX/kg", "market": "Kalerwe"},
                {"crop": "Beans", "price": 3500, "unit": "UGX/kg", "market": "Owino"},
            ]
        })