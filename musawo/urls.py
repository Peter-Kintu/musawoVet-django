# musawo/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from byabulimi import views

urlpatterns = [
    path('', views.index, name='index'),
    path('admin/', admin.site.urls),
    
    # API endpoints for the byabulimi app
    path('api/v1/', include('byabulimi.urls')),
    
    # Web portal URLs
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('query/<int:query_id>/', views.query_detail, name='query_detail'),
    
    # Django authentication URLs
    path('accounts/', include('django.contrib.auth.urls')),
]

# Only serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)