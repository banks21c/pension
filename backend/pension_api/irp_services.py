"""IRP(개인형퇴직연금) 사업자 비교공시 데이터.

주의 — finlife.fss.or.kr(연금저축/예금/적금 등, services.py가 쓰는 API)와
통합연금포털(fss.or.kr/fss/lifeplan, IRP·DB·DC 비교공시)은 완전히 별개 시스템이며
인증키도 서로 다르다. 이 모듈은 통합연금포털 쪽 데이터를 다루는데, 그 API 인증키를
아직 발급받지 못해 fetch_irp_products()는 미구현 상태다.

통합연금포털 Open API가 공개적으로 제공한다고 확인된 4개 비교공시 항목:
  1. 적립금운용현황 — 사업자별 DB/DC/IRP 적립금 및 운용수익률(1·3·5년)
  2. 총비용부담률 — 사업자별 DB/DC/IRP 총비용부담률
  3. 맞춤형 수수료 비교 — 사업자별 수수료율, 기준적립금, 할인정보
  4. 원리금보장상품 제공현황 — 사업자별 제공한도, 적용금리

아래 필드명(bizr_nm 등)은 위 4개 항목 설명을 바탕으로 구성한 잠정 스키마이며,
정식 Open API 문서를 받으면 실제 필드 코드에 맞춰 조정해야 한다. 인증키를 받은
뒤에는 fetch_irp_products()만 구현해서 get_irp_products()의 데이터 소스를
캐시된 실 API 응답으로 바꿔치기하면 프론트엔드/뷰 쪽은 손댈 필요가 없다.
"""
import logging

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

CACHE_KEY = "irp_provider_products"
IRP_PORTAL_BASE_URL = "https://www.fss.or.kr/fss/lifeplan"  # 실 API 엔드포인트 미확정

# 잠정 스키마 예시 데이터 — 실제 사업자 공시치가 아닌 화면 구성용 예시 수치.
_DEMO_PROVIDERS = [
    {
        "bizr_nm": "C증권",
        "pnsn_styl": "IRP",
        "prdt_type_nm": "증권형(실적배당)",
        # 1. 적립금운용현황
        "rsrv_amt_100m": None,      # 사업자 적립금 규모(억원) — 실연동 전 비공개
        "yield_1y_pct": None,       # 운용수익률 1년(%) — 실연동 전 비공개
        "yield_3y_pct": None,
        "yield_5y_pct": None,
        # 2. 총비용부담률
        "tot_cost_brdn_rt_pct": 0.18,
        # 3. 맞춤형 수수료 비교
        "fee_rt_pct": 0.18,
        "std_rsrv_amt_krw": 90_000_000,
        "fee_discount_note": "비대면 개설 시 할인(예시)",
        # 4. 원리금보장상품 제공현황
        "guaranteed_product_offered": False,
        "guaranteed_rate_pct": None,
        "disclosure_month": None,   # 공시기준월(YYYYMM) — 실연동 전 비공개
    },
    {
        "bizr_nm": "A증권",
        "pnsn_styl": "IRP",
        "prdt_type_nm": "증권형(실적배당)",
        "rsrv_amt_100m": None,
        "yield_1y_pct": None,
        "yield_3y_pct": None,
        "yield_5y_pct": None,
        "tot_cost_brdn_rt_pct": 0.25,
        "fee_rt_pct": 0.25,
        "std_rsrv_amt_krw": 90_000_000,
        "fee_discount_note": None,
        "guaranteed_product_offered": False,
        "guaranteed_rate_pct": None,
        "disclosure_month": None,
    },
    {
        "bizr_nm": "B은행",
        "pnsn_styl": "IRP",
        "prdt_type_nm": "은행형(원리금보장)",
        "rsrv_amt_100m": None,
        "yield_1y_pct": None,
        "yield_3y_pct": None,
        "yield_5y_pct": None,
        "tot_cost_brdn_rt_pct": 0.30,
        "fee_rt_pct": 0.30,
        "std_rsrv_amt_krw": 90_000_000,
        "fee_discount_note": None,
        "guaranteed_product_offered": True,
        "guaranteed_rate_pct": None,
        "disclosure_month": None,
    },
    {
        "bizr_nm": "D생명",
        "pnsn_styl": "IRP",
        "prdt_type_nm": "보험형(원리금보장)",
        "rsrv_amt_100m": None,
        "yield_1y_pct": None,
        "yield_3y_pct": None,
        "yield_5y_pct": None,
        "tot_cost_brdn_rt_pct": 0.35,
        "fee_rt_pct": 0.35,
        "std_rsrv_amt_krw": 90_000_000,
        "fee_discount_note": None,
        "guaranteed_product_offered": True,
        "guaranteed_rate_pct": None,
        "disclosure_month": None,
    },
]


def fetch_irp_products(api_key):
    """통합연금포털 Open API에서 IRP 사업자 비교공시 데이터를 받아온다.

    통합연금포털 인증키를 발급받기 전까지는 구현하지 않는다. 발급 후 여기에
    실제 HTTP 호출(및 finlife와 마찬가지로 WAF 우회가 필요하면 curl 위임)을
    구현하고, 응답을 위 _DEMO_PROVIDERS와 동일한 키 구조로 정규화해서 반환하면
    get_irp_products()가 자동으로 실데이터를 쓰게 된다.
    """
    raise NotImplementedError(
        "통합연금포털(fss.or.kr/fss/lifeplan) Open API 인증키가 아직 없습니다. "
        "발급 후 이 함수에 실제 API 호출을 구현하세요."
    )


def get_irp_products(force_refresh=False):
    api_key = getattr(settings, "FSS_LIFEPLAN_API_KEY", "")
    if not api_key:
        return _DEMO_PROVIDERS

    if not force_refresh:
        cached = cache.get(CACHE_KEY)
        if cached is not None:
            return cached

    try:
        products = fetch_irp_products(api_key)
    except NotImplementedError:
        return _DEMO_PROVIDERS

    cache.set(CACHE_KEY, products, timeout=settings.FSS_CACHE_TTL_SECONDS)
    return products
