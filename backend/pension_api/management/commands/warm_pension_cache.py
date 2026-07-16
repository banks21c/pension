from django.core.management.base import BaseCommand

from pension_api.services import get_pension_products


class Command(BaseCommand):
    help = "FSS finlife 연금저축 API를 호출해 캐시를 갱신한다. cron으로 주기 실행 권장."

    def handle(self, *args, **options):
        products = get_pension_products(force_refresh=True)
        self.stdout.write(self.style.SUCCESS(f"연금저축 상품 {len(products)}건 캐시 갱신 완료"))
