"""
Django settings for admire_hrms project.
"""

from pathlib import Path
import os
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,testserver', cast=lambda v: [s.strip() for s in v.split(',')])

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'channels',
    'drf_spectacular',
    'django_celery_beat',
    'django_celery_results',
]

LOCAL_APPS = [
    'apps.core',
    'apps.authentication',
    'apps.employees',
    'apps.attendance',
    'apps.leave_management',
    'apps.payroll',
    'apps.dashboard',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.core.middleware.TenantMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'admire_hrms.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'admire_hrms.wsgi.application'
ASGI_APPLICATION = 'admire_hrms.asgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Redis configuration
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')

# Channels configuration
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [REDIS_URL],
        },
    },
}

# Celery configuration
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes
CELERY_RESULT_EXTENDED = True
CELERY_RESULT_EXPIRES = 3600  # 1 hour
CELERY_WORKER_PREFETCH_MULTIPLIER = 4
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# Celery Beat configuration for scheduled tasks
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Celery Beat schedule (can also be managed via Django admin)
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Monthly payroll generation - runs on 1st of each month at 2 AM
    'monthly-payroll-generation': {
        'task': 'apps.payroll.tasks.monthly_payroll_generation',
        'schedule': crontab(day_of_month='1', hour='2', minute='0'),
    },
    # Initialize annual leave balances - runs on January 1st at 1 AM
    'initialize-annual-leave-balances': {
        'task': 'apps.leave_management.tasks.initialize_annual_leave_balances',
        'schedule': crontab(month_of_year='1', day_of_month='1', hour='1', minute='0'),
    },
    # Send leave balance reminders - runs on 1st of each month at 9 AM
    'send-leave-balance-reminders': {
        'task': 'apps.leave_management.tasks.send_leave_balance_reminder',
        'schedule': crontab(day_of_month='1', hour='9', minute='0'),
    },
    # Send upcoming leave reminders - runs daily at 8 AM
    'send-upcoming-leave-reminders': {
        'task': 'apps.leave_management.tasks.send_upcoming_leave_reminder',
        'schedule': crontab(hour='8', minute='0'),
        'kwargs': {'days_ahead': 7}
    },
    # Send daily attendance summary - runs daily at 6 PM
    'send-daily-attendance-summary': {
        'task': 'apps.attendance.tasks.send_daily_attendance_summary',
        'schedule': crontab(hour='18', minute='0'),
    },
    # Check absent employees - runs daily at 11 AM
    'send-absent-employee-alert': {
        'task': 'apps.attendance.tasks.send_absent_employee_alert',
        'schedule': crontab(hour='11', minute='0'),
    },
    # Calculate monthly attendance summary - runs on 1st of each month at 3 AM
    'calculate-monthly-attendance-summary': {
        'task': 'apps.attendance.tasks.calculate_monthly_attendance_summary',
        'schedule': crontab(day_of_month='1', hour='3', minute='0'),
    },
    # Cleanup old job executions - runs weekly on Sunday at 2 AM
    'cleanup-old-job-executions': {
        'task': 'apps.core.tasks.cleanup_old_job_executions',
        'schedule': crontab(day_of_week='0', hour='2', minute='0'),
        'kwargs': {'days': 30}
    },
    # Health check - runs every 5 minutes
    'health-check': {
        'task': 'apps.core.tasks.health_check_task',
        'schedule': crontab(minute='*/5'),
    },
}

# Email configuration
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@admire-hrms.com')

# Password validation
AUTH_PASSWORD_VALIDATORS = [
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

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'authentication.User'

# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_VERSIONING_CLASS': 'apps.core.versioning.APIVersioning',
    'DEFAULT_VERSION': 'v1',
    'ALLOWED_VERSIONS': ['v1', 'v2'],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'burst': '20/minute',
    },
}

# JWT configuration
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# CORS configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

CORS_ALLOW_CREDENTIALS = True

# API Documentation
SPECTACULAR_SETTINGS = {
    'TITLE': 'Admire HRMS API',
    'DESCRIPTION': 'Comprehensive Human Resource Management System API with multi-tenant support, biometric attendance, leave management, and payroll processing.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'CONTACT': {
        'name': 'Admire HRMS Support',
        'email': 'support@admire-hrms.com',
    },
    'LICENSE': {
        'name': 'Proprietary',
    },
    'SERVERS': [
        {'url': 'http://localhost:8000', 'description': 'Development server'},
        {'url': 'https://api.admire-hrms.com', 'description': 'Production server'},
    ],
    'TAGS': [
        {'name': 'Authentication', 'description': 'User authentication and JWT token management'},
        {'name': 'Employees', 'description': 'Employee management operations'},
        {'name': 'Attendance', 'description': 'Biometric attendance tracking and reporting'},
        {'name': 'Leave Management', 'description': 'Leave requests and approval workflows'},
        {'name': 'Payroll', 'description': 'Payroll processing and salary management'},
        {'name': 'Users', 'description': 'User account management'},
        {'name': 'Roles', 'description': 'Role-based access control'},
        {'name': 'Departments', 'description': 'Department and organizational structure'},
        {'name': 'Dashboard', 'description': 'Real-time metrics and analytics'},
        {'name': 'Core', 'description': 'Core system operations and utilities'},
    ],
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/v1/',
    'SCHEMA_PATH_PREFIX_TRIM': True,
    'PREPROCESSING_HOOKS': [
        'apps.core.api_schema.custom_preprocessing_hook',
    ],
    'POSTPROCESSING_HOOKS': [
        'apps.core.api_schema.custom_postprocessing_hook',
    ],
    'ENUM_NAME_OVERRIDES': {
        'EmployeeStatusEnum': 'apps.employees.models.EMPLOYEE_STATUS_CHOICES',
        'AttendanceStatusEnum': 'apps.attendance.models.ATTENDANCE_STATUS_CHOICES',
        'LeaveStatusEnum': 'apps.leave_management.models.LEAVE_STATUS_CHOICES',
    },
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
        'filter': True,
        'tryItOutEnabled': True,
        'syntaxHighlight.theme': 'monokai',
    },
    'REDOC_UI_SETTINGS': {
        'hideDownloadButton': False,
        'expandResponses': '200,201',
        'pathInMiddlePanel': True,
    },
    'SECURITY': [
        {
            'jwtAuth': [],
        }
    ],
    'APPEND_COMPONENTS': {
        'securitySchemes': {
            'jwtAuth': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
                'description': 'JWT authentication using access tokens. Obtain tokens via /api/v1/auth/login/',
            }
        }
    },
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}