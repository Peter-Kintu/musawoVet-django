# musawo/settings.py

import os
from pathlib import Path
from decouple import config # Recommended for handling environment variables

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- SECURITY SETTINGS ---
# Use django-decouple or similar package to load from a .env file
SECRET_KEY = config('SECRET_KEY', default='django-insecure-k*@^z7t6b7m9v1x0c3y5d2e4f8g0h@i$j!k%l#m&n(o)p^q&r*s')

DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost').split(',')


# --- APPLICATION DEFINITION ---

INSTALLED_APPS = [
   
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # 3rd Party Apps
    'rest_framework', # For building the API endpoints
    
    # Local Apps
    'byabulimi.apps.ByabulimiConfig', # This registers the main app
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'musawo.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'musawo.wsgi.application'
ASGI_APPLICATION = 'musawo.asgi.application'


# --- DATABASE ---
# Using SQLite for simplicity in MVP
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# --- AUTHENTICATION & VALIDATION ---
AUTH_PASSWORD_VALIDATORS = [
    # ... default validators
]


# --- INTERNATIONALIZATION ---
LANGUAGE_CODE = 'en-us' # Base language, actual advice is localized via Gemini
TIME_ZONE = 'Africa/Kampala' 
USE_I18N = True
USE_TZ = True


# --- STATIC & MEDIA FILES ---
STATIC_URL = 'static/'
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media' # Directory for user uploads (images)

# --- CUSTOM CONFIGURATION ---

# 1. Gemini API Key
GEMINI_API_KEY = config('GEMINI_API_KEY') 
# 2. Django REST Framework Settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ]
}

# 3. Default Primary Key Field Type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'