# GA:RAGE — 차량 구독·렌트 큐레이션 플랫폼

Flask + MariaDB로 구현된 풀스택 큐레이션 사이트입니다. 모든 전환(구매·계약·결제)은 카카오톡 1:1 채널에서 일어나며, 사이트는 노출과 문의 유입만 담당합니다.

## 스택

- Backend: Flask 3 + SQLAlchemy + Flask-Migrate + Flask-Login + Flask-WTF
- DB: MariaDB (PyMySQL driver, utf8mb4)
- Frontend: Jinja2 서버 렌더링 + SortableJS (CDN) + Pretendard (CDN)
- 이미지: Pillow (로컬 디스크 → `app/static/uploads/vehicles/{id}/`)
- 배포: Gunicorn + Nginx

상세 명세는 `PROJECT_SPEC_v4.md` 참고.

## 0. 사전 준비 (Windows / MariaDB 로컬 설치)

1. MariaDB Server 11+를 설치합니다.
2. `my.ini`에 다음을 추가하고 서비스 재시작:
   ```
   [mysqld]
   character-set-server = utf8mb4
   collation-server = utf8mb4_unicode_ci
   ```
3. DB와 전용 사용자를 생성합니다 (mysql 클라이언트에서):
   ```sql
   CREATE DATABASE garage DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'garage'@'localhost' IDENTIFIED BY '비밀번호';
   GRANT ALL PRIVILEGES ON garage.* TO 'garage'@'localhost';
   FLUSH PRIVILEGES;
   ```

## 1. 프로젝트 셋업

```powershell
# 1) 가상환경
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2) 의존성
pip install -r requirements.txt

# 3) 환경변수
copy instance\.env.example instance\.env
# instance/.env 를 열어 SECRET_KEY, DB_*, KAKAO_* 값을 채워넣습니다.
# SECRET_KEY 는 다음 명령으로 생성:
#   python -c "import secrets; print(secrets.token_hex(32))"

# 4) 마이그레이션 초기화
$env:FLASK_APP="run.py"
flask db init
flask db migrate -m "initial"
flask db upgrade

# 5) 어드민 + 시드 데이터
flask create-admin                       # 대화형으로 이메일/비밀번호 입력
flask seed-all                           # brands + vehicles + upcoming + faq

# 6) 개발 서버
flask run
```

브라우저에서 http://localhost:5000 접속.

## 2. CLI 명령

| 명령 | 설명 |
|---|---|
| `flask create-admin` | 관리자 계정 생성 (대화형) |
| `flask seed-brands` | 브랜드 마스터 시드 |
| `flask seed-vehicles` | 더미 차량 6대 |
| `flask seed-upcoming` | 업커밍 슬롯 시드 |
| `flask seed-faq` | FAQ 시드 |
| `flask seed-all` | 위 4개 일괄 실행 |

## 3. 디렉토리 개요

```
app/
├── __init__.py            # application factory
├── extensions.py          # db, migrate, login_manager, csrf
├── config.py
├── cli.py
├── models/                # User, Brand, Vehicle, VehicleImage, UpcomingSlot, ...
├── forms/                 # Flask-WTF 폼
├── services/
│   ├── image_service.py   # 업로드 / EXIF / 리사이즈 / 대표 지정
│   ├── upcoming_service.py# UpcomingSlot 트랜잭션 reorder (SSoT)
│   ├── kakao_oauth.py
│   └── site_settings.py   # 캐시된 SiteSetting 접근자
├── blueprints/
│   ├── public/            # /, /vehicles/:id, /upcoming, /faq, /notices
│   ├── auth/              # /auth/login, /auth/signup, /auth/kakao(...)
│   ├── mypage/            # /mypage
│   ├── admin/             # /admin/* (admin_required)
│   └── api/               # /api/*
├── templates/
│   ├── base.html          # 공통 레이아웃 (헤더/푸터/플로팅 카카오)
│   ├── public/...
│   ├── auth/login.html    # 로그인+회원가입 탭 전환
│   ├── mypage/index.html
│   ├── admin/admin_base.html (사이드바)
│   └── admin/*.html
└── static/
    ├── css/{tokens,site,admin}.css
    ├── js/{common,hero,slider,gallery,faq,upcoming-order,vehicle-form,auth,favorite}.js
    └── uploads/{_tmp,vehicles}/
```

## 4. 핵심 설계 결정

- **UpcomingSlot 단일 진실 공급원**: 업커밍 페이지 노출과 순서는 오직 `UpcomingSlot` 테이블에서 관리. `Vehicle.placement`는 `collection / none`만 의미.
- **CSRF on JSON**: `base.html`에 `<meta name="csrf-token">` 삽입 + `common.js`의 `apiFetch()`가 모든 비-GET 요청에 `X-CSRFToken` 헤더를 자동 첨부.
- **이미지 업로드**: 신규 차량은 일단 기본 정보만 저장한 뒤 수정 화면에서 이미지를 업로드합니다 (디렉토리 타이밍 문제 회피).
- **OAuth state**: `secrets.token_urlsafe(32)` 생성 후 `session['kakao_state']`에 저장, 콜백에서 비교 후 삭제 (CSRF 방어).
- **가격 포맷**: `{{ price_min_man | price_man(price_max_man) }}` — 최저가만 있으면 `월 239만원`, 최고가가 다르면 범위.

## 5. 검증 체크리스트 (Sprint별)

### Sprint 1
- [ ] `flask run` 정상 부팅
- [ ] http://localhost:5000 메인 페이지 디자인 그대로 렌더링
- [ ] PC(≥1024px)에서 차량 슬라이더 좌우 화살표 동작
- [ ] 모바일(<768px)에서 1열, 태블릿 2열
- [ ] 차량 상세 페이지 갤러리 썸네일 클릭 동작
- [ ] 플로팅 카카오 버튼이 모든 공개 페이지에 표시 (차량 상세 모바일 제외)

### Sprint 2
- [ ] /admin 비로그인 접근 시 /auth/login으로 리다이렉트
- [ ] 일반 회원으로 /admin 접근 시 403
- [ ] /admin/vehicles/new 등록 → /admin/vehicles/:id/edit 로 이동
- [ ] 이미지 5장 업로드 → 대표 지정 → 드래그 순서 변경 → DB 반영 확인
- [ ] /admin/upcoming/order 드래그 → 우하단 토스트 → 새로고침해도 순서 유지
- [ ] DevTools Network에서 PATCH /admin/api/upcoming/order 요청 + X-CSRFToken 헤더 확인
- [ ] Notice/FAQ CRUD 정상 동작

### Sprint 3
- [ ] /auth/signup 일반 가입 → 자동 로그인 → /mypage 진입
- [ ] 차량 카드 ♡ 토글 → 새로고침 후에도 유지
- [ ] /auth/kakao state 변조 테스트 (URL state 파라미터 수정) → /auth/login 으로 리다이렉트 + flash
- [ ] /upcoming 페이지가 어드민 순서대로 노출

### Sprint 4
- [ ] 4개 브레이크포인트(375/768/1024/1280) 스크린샷 점검
- [ ] Lighthouse 모바일 90+
- [ ] gunicorn 으로 `wsgi:application` 띄우고 동작 확인

## 6. 배포 (참고)

```bash
gunicorn -w 4 -b 127.0.0.1:8000 wsgi:application
```

Nginx에서 `/static/` 은 직접 서빙, 나머지는 gunicorn upstream으로 프록시.

## 7. 주의사항 (PROJECT_SPEC_v4.md 10절)

- 결제·계약·심사 흐름을 절대 추가하지 말 것. 모든 전환은 카카오 채널로.
- 어드민 업커밍 순서 저장은 드래그 종료 즉시 PATCH (debounce 300ms). 별도 저장 버튼 두지 말 것.
- 디자인 토큰을 임의로 바꾸지 말 것 (`app/static/css/tokens.css`).
- 차량 상세 모바일에서 플로팅 카카오 버튼은 하단 고정 CTA와 겹치므로 노출 안 함.
