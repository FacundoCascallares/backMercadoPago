# Django settings for backend project.

from pathlib import Path
import os

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'tu-clave-secreta-por-defecto')

# === CONFIGURACIÓN BASE (APLICABLE A AMBOS ENTORNOS) ===
# Application definition
INSTALLED_APPS = [
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'accounts.apps.AccountsConfig',
    'core',
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',  # si estás usando un modelo personalizado, revisá si usás otro
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'backend.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'es-ar'
TIME_ZONE = 'America/Buenos_Aires'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'users')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ]
}

# Credenciales de Mercado Pago
# Para producción, usa variables de entorno: os.environ.get("MP_ACCESS_TOKEN")
MERCADOPAGO_ACCESS_TOKEN = 'APP_USR-6112707204413529-051922-88ebe4c9479cd3495fbb9a6734499bbf-174672931'
MERCADOPAGO_PUBLIC_KEY = 'APP_USR-14983d03-9340-4815-ac9b-3ade487b5510' 


# === CONFIGURACIÓN ESPECÍFICA PARA PRODUCCIÓN (PythonAnywhere) ===
if 'PYTHONANYWHERE_DOMAIN' in os.environ:
    DEBUG = False
    # Define ALLOWED_HOSTS para producción
    ALLOWED_HOSTS = [
        'dreamtravel.pythonanywhere.com',
        'www.dreamtravel.pythonanywhere.com',
        os.environ.get('PYTHONANYWHERE_DOMAIN', ''), # Usa .get para evitar KeyError
        f"www.{os.environ.get('PYTHONANYWHERE_DOMAIN', '')}"
    ]
    # Define BACKEND_BASE_URL para producción
    BACKEND_BASE_URL = 'http://localhost:4200/' 


    # CORS Settings (para PRODUCCIÓN en PythonAnywhere)
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:4200/",  # Reemplaza con tu dominio real
        # Si tu frontend también está en PythonAnywhere y usa un subdominio, agrégalo aquí
        # Por ejemplo: "https://tu-frontend.pythonanywhere.com"
    ]
    CORS_EXPOSE_HEADERS = ['Content-Type', 'X-CSRFToken']
    CORS_ALLOW_CREDENTIALS = True
    CORS_ALLOW_METHODS = [
        'DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT',
    ]
    CORS_ALLOW_HEADERS = [
        'accept', 'accept-encoding', 'authorization', 'content-type', 'dnt',
        'origin', 'user-agent', 'x-csrftoken', 'x-requested-with',
    ]
    
    # Security Headers (para PRODUCCIÓN)
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    X_FRAME_OPTIONS = 'DENY'
    
# === CONFIGURACIÓN ESPECÍFICA PARA DESARROLLO LOCAL ===
else: # Esto se ejecuta cuando 'PYTHONANYWHERE_DOMAIN' NO está en os.environ (es decir, en local)
    DEBUG = True 
    # Define ALLOWED_HOSTS para desarrollo local (incluyendo ngrok)
    # ¡Aquí es donde debes añadir la URL de ngrok TEMPORALMENTE!
    # Nota: La URL de ngrok (caf4-201-179-84-139.ngrok-free.app) cambia cada vez que lo inicias.
    # Debes actualizarla aquí manualmente cada vez que inicies ngrok si cambias de URL.
    ALLOWED_HOSTS = [
        'localhost',
        '127.0.0.1',
        'caf4-201-179-84-139.ngrok-free.app', # <-- ¡Esta es la clave para que funcione con ngrok!
        # Puedes añadir más IPs si pruebas desde otras máquinas en tu red local.
    ]

    # CORS Settings (para DESARROLLO local)
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:4200", # Tu frontend local
        "http://127.0.0.1:4200", # Tu frontend local

    ]
    CORS_EXPOSE_HEADERS = ['Content-Type', 'X-CSRFToken']
    CORS_ALLOW_CREDENTIALS = True
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOW_METHODS = [
        'DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT',
    ]
    CORS_ALLOW_HEADERS = [
        'accept', 'accept-encoding', 'authorization', 'content-type', 'dnt',
        'origin', 'user-agent', 'x-csrftoken', 'x-requested-with',
    ]

    # Security Headers (para DESARROLLO)
    # ¡Desactivadas o ajustadas para HTTP!
    SECURE_PROXY_SSL_HEADER = None 
    SESSION_COOKIE_SECURE = False 
    CSRF_COOKIE_SECURE = False    
    SECURE_SSL_REDIRECT = False   
    SECURE_HSTS_SECONDS = 0       
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
    X_FRAME_OPTIONS = 'SAMEORIGIN'