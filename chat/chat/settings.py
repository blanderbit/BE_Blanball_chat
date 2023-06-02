from typing import Any
from os import path
from pathlib import Path
from decouple import Csv, config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Application definition

INSTALLED_APPS: list[str] = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE: list[str] = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'chat.urls'

TEMPLATES: list[dict[str, Any]] = [
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

WSGI_APPLICATION: str = 'chat.wsgi.application'


DATABASES: dict[str, Any] = {
    "default": {
        "ENGINE": config("DB_ENGINE", cast=str),
        "NAME": config("POSTGRES_DB", cast=str),
        "USER": config("POSTGRES_USER", cast=str),
        "PASSWORD": config("POSTGRES_PASSWORD", cast=str),
        "HOST": config("POSTGRES_HOST", cast=str),
        "PORT": config("POSTGRES_PORT", cast=int),
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS: list[dict[str, Any]] = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# project secret key
SECRET_KEY: str = config("SECRET_KEY", cast=str)

# list of allowed project hosts
ALLOWED_HOSTS: list[str] = config("ALLOWED_HOSTS", cast=Csv())
################################################################

# the path where you can open any static file
# from the directory STATIC_ROOT in the browser
STATIC_URL: str = "/static/"

# the path to the folder where all static files, styles, etc. are saved
STATIC_ROOT: str = path.join(BASE_DIR, "static/")

# path to the file that is responsible
# for processing synchronous requests to the application
WSGI_APPLICATION: str = "config.wsgi.application"
# path to the file that is responsible for
# processing asynchronous requests to the application

ASGI_APPLICATION: str = "config.asgi.application"

# path to a file that contains all the application's routing paths
ROOT_URLCONF: str = "config.urls"

# the constant that is responsible for which
# locale is currently set in the application
LANGUAGE_CODE: str = config("LANGUAGE_CODE", cast=str)

# the constant responsible for the time
# zone in which the application will work
TIME_ZONE: str = config("TIME_ZONE", cast=str)

USE_I18N: bool = config("USE_I18N", cast=bool)

USE_TZ: bool = False

USE_L10N: bool = True

# the constant that is responsible for filling the id field
DEFAULT_AUTO_FIELD: str = "django.db.models.BigAutoField"

# the constant that is responsible for the mode in which the application will work.
# if true will be the development mode.
# if false, then in prod server mode
DEBUG: bool = config("DEBUG", cast=bool)


DEFAULT_AUTO_FIELD: str = 'django.db.models.BigAutoField'
