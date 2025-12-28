# byabulimi/views.py (Updated with Gemini Integration)

import base64
from decimal import Decimal
from django.core.files.base import ContentFile
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .models import Farmer, Query, Advice
from .serializers import (
    FarmerRegisterSerializer, FarmerProfileSerializer, 
    QuerySubmitSerializer, QueryHistorySerializer
)
# Import the Gemini function and the file helper from our AI service layer
from .ai_service import generate_diagnosis, file_to_part

# --- Web Views for Admin/Staff Portal ---

def index(request):
    """Simple homepage view."""
    return render(request, 'index.html')

@login_required
def dashboard(request):
    """Web dashboard showing recent activity for the logged-in farmer."""
    try:
        farmer = request.user.farmer
        recent_queries = Query.objects.filter(farmer=farmer).order_by('-timestamp')[:5]
        context = {
            'farmer': farmer,
            'recent_queries': recent_queries,
        }
        return render(request, 'byabulimi/dashboard.html', context)
    except Farmer.DoesNotExist:
        messages.error(request, 'Farmer profile not found.')
        return redirect('index')

@login_required
def profile(request):
    """View to manage farmer profile settings via web."""
    try:
        farmer = request.user.farmer
        context = {'farmer': farmer}
        return render(request, 'byabulimi/profile.html', context)
    except Farmer.DoesNotExist:
        messages.error(request, 'Farmer profile not found.')
        return redirect('index')

@login_required
def query_detail(request, query_id):
    """Detailed view for a specific diagnostic query."""
    try:
        farmer = request.user.farmer
        query = get_object_or_404(Query, id=query_id, farmer=farmer)
        # Attempt to get advice; if AI hasn't responded, it will be None
        advice = getattr(query, 'advice', None)
        context = {
            'query': query,
            'advice': advice,
        }
        return render(request, 'byabulimi/query_detail.html', context)
    except Farmer.DoesNotExist:
        messages.error(request, 'Farmer profile not found.')
        return redirect('index')


# --- 1. Authentication & Profile API Views ---

class FarmerRegisterAPIView(generics.CreateAPIView):
    """Handles new farmer registration (User + Farmer profile creation)."""
    queryset = Farmer.objects.all()
    serializer_class = FarmerRegisterSerializer
    permission_classes = [permissions.AllowAny]

class FarmerProfileAPIView(generics.RetrieveAPIView):
    """Retrieves current profile data for the mobile app."""
    serializer_class = FarmerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        try:
            return self.request.user.farmer
        except Farmer.DoesNotExist:
            return None


# --- 2. Core Diagnostic Query API Views ---

class QuerySubmitAPIView(generics.CreateAPIView):
    """
    Primary endpoint for the Flutter app. 
    Receives image/text, saves locally, calls Gemini, and returns diagnosis.
    """
    serializer_class = QuerySubmitSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def _create_advice(self, query: Query, diagnosis_output: dict):
        """Helper to convert Gemini's JSON output into a Django Advice object."""
        
        # We extract 'localized_advice_luganda' but fall back to summary if missing
        advice_text = diagnosis_output.get("localized_advice_luganda") or \
                     diagnosis_output.get("english_summary") or "No advice returned."

        return Advice.objects.create(
            query=query,
            diagnosis_code=diagnosis_output.get("diagnosis_code"),
            # Convert float/int from AI to Decimal for high-precision model storage
            confidence_score=Decimal(str(diagnosis_output.get("confidence_score", 0.0))),
            localized_advice=advice_text,
            is_expert_referred=diagnosis_output.get("is_expert_referral_needed", False),
            english_summary=diagnosis_output.get("english_summary")
        )

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 1. Extract Validated Data
        base64_data = serializer.validated_data.get('image_base64')
        query_text = serializer.validated_data.get('query_text')
        detected_crop = serializer.validated_data.get('detected_crop')
        farmer = self.request.user.farmer

        # 2. Decode Image for Local Storage
        try:
            image_bytes = base64.b64decode(base64_data)
            image_file = ContentFile(
                image_bytes, 
                name=f'{farmer.phone_number}_{detected_crop}_query.jpg'
            )
        except Exception as e:
            return Response(
                {"message": f"Malformed image data: {e}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Create Local Database Entry
        new_query = Query.objects.create(
            farmer=farmer,
            image=image_file,
            raw_query_text=query_text,
            detected_crop=detected_crop,
        )
        
        # 4. Multimodal AI Processing
        # Convert raw bytes to Gemini-compatible Part
        image_part = file_to_part(image_bytes)
        
        diagnosis_output = generate_diagnosis(
            image_part=image_part, 
            query_text=query_text, 
            detected_crop=detected_crop, 
            language_code=farmer.language_code
        )
        
        # 5. Link AI Advice to Query
        advice_instance = self._create_advice(new_query, diagnosis_output)

        # 6. Structured Synchronous Response (Matches Flutter 'DiagnosisResponse')
        return Response({
            "query_id": new_query.id,
            "message": "Diagnosis generated successfully.",
            "localized_advice": advice_instance.localized_advice,
            "english_summary": advice_instance.english_summary,
            "confidence_score": float(advice_instance.confidence_score),
            "is_expert_referred": advice_instance.is_expert_referred,
            "diagnosis_code": advice_instance.diagnosis_code,
        }, status=status.HTTP_201_CREATED) 

class QueryHistoryAPIView(generics.ListAPIView):
    """Returns a list of all past queries and their results for the farmer."""
    serializer_class = QueryHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Query.objects.filter(farmer=self.request.user.farmer).order_by('-timestamp')


# --- 3. Market & Weather Data Views (Regional Stubs) ---

class WeatherAlertsAPIView(generics.RetrieveAPIView):
    """Returns regional weather risks based on the farmer's registered region."""
    permission_classes = [permissions.IsAuthenticated]
    
    def retrieve(self, request, *args, **kwargs):
        # Stub: Integration with OpenWeather or similar would happen here
        return Response({
            "region": request.user.farmer.region,
            "forecast_7_day": "Light rain expected; good for planting maize.",
            "pest_risk": "Low risk for current season.",
        })

class MarketPricesAPIView(generics.RetrieveAPIView):
    """Returns live local market prices for crops/livestock."""
    permission_classes = [permissions.IsAuthenticated]
    
    def retrieve(self, request, *args, **kwargs):
        # Stub: Data would be pulled from a scraped or API-driven market database
        return Response({
            "region": request.user.farmer.region,
            "prices": [
                {"crop": "Maize", "price": 1200, "unit": "UGX/kg", "market": "Kalerwe"},
                {"crop": "Beans", "price": 3500, "unit": "UGX/kg", "market": "Owino"},
            ]
        })