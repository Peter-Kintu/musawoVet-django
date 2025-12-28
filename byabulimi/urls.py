# byabulimi/urls.py

from django.urls import path
from . import views
from rest_framework.authtoken.views import obtain_auth_token

app_name = 'byabulimi'

urlpatterns = [
    # --- 1. Authentication & Profile ---
    # Standard Token Auth: returns {'token': '...'}
    path('auth/login/', obtain_auth_token, name='api_token_auth'),
    
    # Custom registration that creates both User and Farmer profile
    path('farmers/register/', views.FarmerRegisterAPIView.as_view(), name='farmer-register'),
    
    # View to retrieve or update the authenticated farmer's details
    path('farmers/profile/', views.FarmerProfileAPIView.as_view(), name='farmer-profile'),
    
    # --- 2. Core Diagnostic Query ---
    # Endpoint where the Flutter app posts image_base64 and metadata
    path('queries/submit/', views.QuerySubmitAPIView.as_view(), name='query-submit'),
    
    # Endpoint to fetch the history of diagnoses for the logged-in farmer
    path('queries/history/', views.QueryHistoryAPIView.as_view(), name='query-history'),
    
    # --- 3. Market & Weather Data ---
    # Weather alerts based on the farmer's registered region
    path('data/weather/', views.WeatherAlertsAPIView.as_view(), name='data-weather'),
    
    # Market prices for crops and livestock
    path('markets/prices/', views.MarketPricesAPIView.as_view(), name='market-prices'),
]