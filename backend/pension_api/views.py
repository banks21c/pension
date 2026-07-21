import json
import logging
from datetime import datetime, timezone

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from .services import get_pension_products

logger = logging.getLogger(__name__)


@require_GET
def pension_products(request):
    force_refresh = request.GET.get("refresh") == "1"
    products = get_pension_products(force_refresh=force_refresh)

    pnsn_kind = request.GET.get("pnsn_kind")
    if pnsn_kind:
        products = [p for p in products if p.get("pnsn_kind_nm") == pnsn_kind]

    return JsonResponse({"count": len(products), "products": products})


CONSULT_LOG_PATH = settings.BASE_DIR / "var" / "consults.jsonl"
CONSULT_RATE_LIMIT_SECONDS = 30


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


@require_POST
def consult_submit(request):
    """index.html / irp_upgraded.html의 상담 신청 폼이 호출하는 엔드포인트.
    DB가 없는 구성이라 var/consults.jsonl에 한 줄씩 append하고, 파일캐시로 IP당 레이트리밋만 건다."""
    website = (request.POST.get("website") or "").strip()
    if website:
        # 허니팟 필드가 채워져 있으면 봇으로 간주. 봇에게 실패를 티내지 않기 위해 성공으로만 응답하고 저장하지 않는다.
        logger.info("상담 신청 스팸(허니팟) 차단: ip=%s", _client_ip(request))
        return JsonResponse({"ok": True})

    name = (request.POST.get("name") or "").strip()
    phone = (request.POST.get("phone") or "").strip()
    if not name or not phone:
        return JsonResponse({"ok": False, "error": "이름과 연락처는 필수입니다."}, status=400)

    consent = (request.POST.get("consent") or "").strip()
    if not consent:
        return JsonResponse({"ok": False, "error": "개인정보 수집·이용에 동의해야 신청할 수 있습니다."}, status=400)

    ip = _client_ip(request)
    rate_key = f"consult_rate:{ip}"
    if cache.get(rate_key):
        return JsonResponse({"ok": False, "error": "잠시 후 다시 시도해주세요."}, status=429)
    cache.set(rate_key, True, timeout=CONSULT_RATE_LIMIT_SECONDS)

    entry = {
        "received_at": datetime.now(timezone.utc).isoformat(),
        "ip": ip,
        "product": (request.POST.get("product") or "").strip(),
        "name": name,
        "phone": phone,
        "interest": (request.POST.get("interest") or "").strip(),
        "goal": (request.POST.get("goal") or "").strip(),
        "message": (request.POST.get("message") or "").strip(),
        "consent": True,
    }

    CONSULT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CONSULT_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    logger.info("상담 신청 접수: product=%s name=%s", entry["product"], name)
    return JsonResponse({"ok": True})
