# byabulimi/urls.py

from django.urls import path
from . import views
from rest_framework.authtoken.views import obtain_auth_token

# Define URL patterns for the API
urlpatterns = [
    # 1. Authentication & Profile
    # Placeholder: We will use a custom login/register view for phone number logic later.
    path('auth/login/', obtain_auth_token, name='api_token_auth'),
    path('farmers/register/', views.FarmerRegisterAPIView.as_view(), name='farmer-register'),
    path('farmers/profile/', views.FarmerProfileAPIView.as_view(), name='farmer-profile'),
    
    # 2. Core Diagnostic Query
    path('queries/submit/', views.QuerySubmitAPIView.as_view(), name='query-submit'),
    path('queries/history/', views.QueryHistoryAPIView.as_view(), name='query-history'),
    
    # 3. Market & Weather Data (Stubs for now)
    path('data/weather/', views.WeatherAlertsAPIView.as_view(), name='data-weather'),
    path('data/markets/', views.MarketPricesAPIView.as_view(), name='data-markets'),
]