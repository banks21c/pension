# pension backend

금감원 금융상품통합비교공시(finlife) 오픈API에서 연금저축 상품 목록을 가져와
`GET /api/pension/products/`로 제공하는 Django 앱.

## 로컬 실행

```bash
cd backend
../pension_venv/bin/pip install -r requirements.txt
cp .env.example .env   # FSS_FINLIFE_API_KEY 채워넣기
../pension_venv/bin/python manage.py runserver 127.0.0.1:8001
curl http://127.0.0.1:8001/api/pension/products/
```

## 알려진 이슈: FSS API 키 승인 대기

`FSS_FINLIFE_API_KEY`는 예금상품 API(`depositProductsSearch`)에서는 정상 동작하지만,
연금저축 API(`annuitySavingProductsSearch`)에서는 아직 실제 데이터를 반환하지 않는다
(응답은 `err_cd=000`으로 정상이나 상품군과 무관한 데이터가 섞여 오거나 목록이 비어 있음).
금감원 오픈API 포털(finlife.fss.or.kr)에서 이 키의 **연금저축 API 이용 승인 여부**를
확인해야 한다. 승인되면 코드 변경 없이 바로 정상 데이터가 내려온다.

승인 전까지는 프런트엔드(`index.html`)는 기존 데모 데이터를 그대로 사용한다.

## 캐시

FSS 공시자료는 월 단위로 갱신되므로 결과를 파일 기반 캐시에 `FSS_CACHE_TTL_SECONDS`(기본 6시간)
동안 저장한다. 첫 요청이 FSS 호출 지연을 떠안지 않도록 cron으로 미리 데워두는 것을 권장:

```
0 * * * * /srv/pension/pension_venv/bin/python /srv/pension/backend/manage.py warm_pension_cache
```

## 배포

`deploy/pension-api.service`(systemd, gunicorn) + `deploy/nginx-pension-api.conf`
(nextfinup.com을 서빙하는 기존 nginx server 블록에 병합할 `/api/pension/` 리버스 프록시
조각) 참고. 실제 서버 nginx 설정은 이 저장소에 없으므로 서버에서 직접 확인 후 적용할 것.
