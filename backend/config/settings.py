from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-only-insecure-key")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# 금융감독원 금융상품통합비교공시(finlife) 오픈API 인증키 — 예금/적금/연금저축/대출 상품
# https://finlife.fss.or.kr 에서 발급, API별로 별도 승인이 필요할 수 있음
FSS_FINLIFE_API_KEY = env("FSS_FINLIFE_API_KEY")

# 통합연금포털 오픈API 인증키 — IRP/DB/DC 퇴직연금 사업자 비교공시 (finlife와 별개 시스템)
# https://www.fss.or.kr/fss/lifeplan 에서 별도 발급 필요. 미발급 상태에서는 빈 문자열로 두면
# irp_services.get_irp_products()가 자동으로 데모 데이터를 반환한다.
FSS_LIFEPLAN_API_KEY = env("FSS_LIFEPLAN_API_KEY", default="")

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "pension_api",
]

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {}

LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": str(BASE_DIR / "var" / "cache"),
    }
}

# FSS finlife 공시자료는 월 단위로 갱신되므로 캐시를 길게 잡아 API 호출을 아낀다.
FSS_CACHE_TTL_SECONDS = env.int("FSS_CACHE_TTL_SECONDS", default=6 * 60 * 60)
