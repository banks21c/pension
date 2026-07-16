import json
import logging
import subprocess
from urllib.parse import urlencode

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

FSS_ANNUITY_SAVINGS_URL = "https://finlife.fss.or.kr/finlifeapi/annuitySavingProductsSearch.json"

# 연금저축을 취급하는 금융권역: 은행, 보험, 금융투자(증권)
TOP_FIN_GRP_NOS = ["020000", "050000", "060000"]

CACHE_KEY = "fss_annuity_savings_products"


class FssApiError(Exception):
    pass


def _curl_get_json(url, params, timeout=10):
    """finlife.fss.or.kr는 WAF가 python-requests/urllib3의 TLS·헤더 지문을 막아
    연결을 그냥 끊어버린다(RemoteDisconnected). curl은 통과하므로 그대로 위임한다."""
    full_url = f"{url}?{urlencode(params)}"
    try:
        proc = subprocess.run(
            ["curl", "-sS", "-A", "Mozilla/5.0", "--max-time", str(timeout), full_url],
            capture_output=True,
            timeout=timeout + 5,
            check=True,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as exc:
        raise FssApiError(f"curl 호출 실패: {exc}") from exc

    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise FssApiError(f"FSS 응답 JSON 파싱 실패: {exc}") from exc


def _fetch_group(group_no, api_key):
    """topFinGrpNo 하나에 대해 모든 페이지를 모아 (baseList, optionList) 튜플로 반환."""
    base_rows = []
    option_rows = []
    page_no = 1
    max_page_no = 1

    while page_no <= max_page_no:
        data = _curl_get_json(
            FSS_ANNUITY_SAVINGS_URL,
            {"auth": api_key, "topFinGrpNo": group_no, "pageNo": page_no},
        )
        payload = data.get("result", {})

        err_cd = payload.get("err_cd")
        if err_cd and err_cd != "000":
            raise FssApiError(f"FSS API error {err_cd}: {payload.get('err_msg')}")

        max_page_no = payload.get("max_page_no") or 1
        page_base = payload.get("baseList") or []
        page_options = payload.get("optionList") or []

        # 관찰된 이슈: 일부 권역/키 조합에서 err_cd=000(정상)이지만 baseList가
        # 비어 있거나(승인 대기 등) 연금저축과 무관한 스키마(예: 대출상품)가 오는 경우가 있다.
        # 연금저축 데이터는 baseList 각 항목에 pnsn_kind_nm이 있어야 하므로, 없는 항목은
        # 다른 API 응답이 잘못 섞인 것으로 보고 건너뛰고 경고를 남긴다.
        valid_base = [row for row in page_base if "pnsn_kind_nm" in row]
        skipped = len(page_base) - len(valid_base)
        if skipped:
            logger.warning(
                "FSS annuitySavingProductsSearch: topFinGrpNo=%s pageNo=%s "
                "%d개 항목이 연금저축 스키마가 아니어서 제외됨 (API 키의 해당 상품군 승인 여부 확인 필요)",
                group_no, page_no, skipped,
            )

        base_rows.extend(valid_base)
        option_rows.extend(page_options)
        page_no += 1

    return base_rows, option_rows


def _normalize(base_row, options_by_key):
    key = (base_row.get("fin_co_no"), base_row.get("fin_prdt_cd"))
    return {
        "fin_co_no": base_row.get("fin_co_no"),
        "kor_co_nm": base_row.get("kor_co_nm"),
        "fin_prdt_cd": base_row.get("fin_prdt_cd"),
        "fin_prdt_nm": base_row.get("fin_prdt_nm"),
        "pnsn_kind_nm": base_row.get("pnsn_kind_nm"),
        "prdt_type_nm": base_row.get("prdt_type_nm"),
        "join_way": base_row.get("join_way"),
        "sale_strt_day": base_row.get("sale_strt_day"),
        # 펀드형 지표
        "avg_prft_rate": base_row.get("avg_prft_rate"),
        "btrm_prft_rate_1": base_row.get("btrm_prft_rate_1"),
        "btrm_prft_rate_2": base_row.get("btrm_prft_rate_2"),
        "btrm_prft_rate_3": base_row.get("btrm_prft_rate_3"),
        # 보험형 지표
        "dcls_rate": base_row.get("dcls_rate"),
        "guar_rate": base_row.get("guar_rate"),
        "sale_co": base_row.get("sale_co"),
        "dcls_month": base_row.get("dcls_month"),
        "dcls_strt_day": base_row.get("dcls_strt_day"),
        "dcls_end_day": base_row.get("dcls_end_day"),
        "options": options_by_key.get(key, []),
    }


def fetch_pension_products():
    """FSS finlife 연금저축 오픈API에서 전 권역 상품을 받아 정규화된 리스트로 반환한다."""
    api_key = settings.FSS_FINLIFE_API_KEY
    products = []

    for group_no in TOP_FIN_GRP_NOS:
        try:
            base_rows, option_rows = _fetch_group(group_no, api_key)
        except FssApiError as exc:
            logger.error("FSS annuitySavingProductsSearch 호출 실패 (topFinGrpNo=%s): %s", group_no, exc)
            continue

        options_by_key = {}
        for opt in option_rows:
            key = (opt.get("fin_co_no"), opt.get("fin_prdt_cd"))
            options_by_key.setdefault(key, []).append(opt)

        for base_row in base_rows:
            product = _normalize(base_row, options_by_key)
            product["top_fin_grp_no"] = group_no
            products.append(product)

    return products


def get_pension_products(force_refresh=False):
    if not force_refresh:
        cached = cache.get(CACHE_KEY)
        if cached is not None:
            return cached

    products = fetch_pension_products()
    cache.set(CACHE_KEY, products, timeout=settings.FSS_CACHE_TTL_SECONDS)
    return products
