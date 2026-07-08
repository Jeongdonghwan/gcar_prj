# 차량 구독 플랫폼 — 개발 명세서

> **개발 방식**: Claude Code 사용
> **디자인 컨셉**: 친근한 e-commerce 톤 (rerev.kr 참고)
> **이 문서의 목적**: 디자인 HTML 초안과 함께 Claude Code가 풀스택 구현을 단독 진행할 수 있도록 모든 의사결정을 단일 문서로 정리

---

## 1. 서비스 개요

### 1.1 핵심 가치 제안
- 차량 구독·렌트 상품을 큐레이션해서 보여주고, 모든 전환은 **카카오톡 1:1 문의**로 클로징
- 사이트 내 결제·계약·심사 흐름 **일체 없음**
- 어드민이 직접 차량을 등록하고, 업커밍 페이지에 노출되는 차량의 순서를 임의 배치

### 1.2 사이트 맵

| 경로 | 화면 |
|---|---|
| `/` | 메인 (히어로, 빠른 진입 카드, 차량 슬라이더) |
| `/vehicles/:id` | 차량 상세 |
| `/upcoming` | 업커밍 리스트 (어드민 정렬 순) |
| `/faq` | 고객센터 (카카오 1:1, 공지, FAQ) |
| `/notices`, `/notices/:id` | 공지사항 |
| `/login`, `/signup` | 로그인·회원가입 (탭 전환 / 카카오싱크 + 일반) |
| `/mypage` | 마이페이지 (찜, 회원정보) |
| `/terms/service`, `/terms/privacy` | 약관 |
| `/admin` | 어드민 대시보드 |
| `/admin/vehicles`, `/admin/vehicles/new`, `/admin/vehicles/:id/edit` | 차량 관리 |
| `/admin/upcoming/order` | 업커밍 순서 관리 (드래그앤드롭) |
| `/admin/notices`, `/admin/faq`, `/admin/users` | 콘텐츠·회원 관리 |

### 1.3 사용자 역할
| 역할 | 권한 |
|---|---|
| 게스트 | 공개 페이지 조회, 카카오 문의, 회원가입 |
| 회원 | 게스트 + 찜, 마이페이지 |
| 관리자 | 회원 + `/admin/*` 전 영역 |

---

## 2. 기술 스택

| 레이어 | 선택 |
|---|---|
| 백엔드 | **Flask** (Blueprint: public / auth / mypage / admin) |
| DB | **MariaDB** + SQLAlchemy ORM |
| 프론트엔드 | **React (Vite) 권장** — 이 디자인 초안은 Vanilla HTML로 작성됨. Jinja2로 가도 무방 |
| 인증 | Flask-Login + 카카오 OAuth (Kakao Sync) |
| 이미지 | 로컬 디스크 `/static/uploads/vehicles/{id}/` → 추후 R2/S3 |
| 폼/CSRF | Flask-WTF |
| 드래그앤드롭 | **SortableJS** (CDN) |
| 배포 | Gunicorn + Nginx |

### 2.1 디렉토리 구조

```
project/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── models/          # User, Vehicle, VehicleImage, UpcomingSlot, Notice, FAQ, Inquiry, Favorite, SiteSetting
│   ├── blueprints/
│   │   ├── public/      # 메인, 차량 상세, 업커밍, FAQ, 공지
│   │   ├── auth/        # 로그인, 회원가입, 카카오 콜백
│   │   ├── mypage/
│   │   └── admin/       # 어드민 전체
│   ├── services/        # KakaoService, ImageUploadService
│   ├── templates/       # (Jinja2 사용 시)
│   └── static/css, js, uploads
├── migrations/
├── requirements.txt
└── run.py
```

---

## 3. 디자인 시스템

### 3.1 컬러 토큰

```css
:root {
  /* Surface */
  --bg: #FFFFFF;            /* 페이지 배경 */
  --surface: #F4F6F9;       /* 카드 배경 */
  --surface-2: #EDF0F5;     /* 카드 hover */
  
  /* Text */
  --ink: #111111;           /* 본문, 헤딩 */
  --ink-2: #4B5563;         /* 보조 */
  --muted: #8B92A0;         /* 캡션, 비활성 */
  
  /* Lines */
  --line: #E5E7EB;
  --line-2: #EEF1F5;
  
  /* Brand */
  --primary: #3B6EF5;       /* 메인 파랑 (액센트, CTA 보조) */
  --primary-soft: #E8F0FF;
  --primary-deep: #2952CC;
  
  /* Functional */
  --warn: #FF6A3D;          /* 특가, 강조 */
  --success: #1FA363;
  
  /* Kakao (변경 금지) */
  --kakao: #FEE500;
  --kakao-ink: #3A1D1D;
}
```

### 3.2 타이포그래피

- **폰트 단일화**: Pretendard 한 종류만 사용
  - CDN: `https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css`
- 영문 표현은 wider letter-spacing(-0.025em ~ -0.04em)을 통해 모던하게
- 숫자는 `font-variant-numeric: tabular-nums`로 일관성 유지

타이포 스케일 (모바일 → PC):

| 용도 | 모바일 | PC |
|---|---|---|
| 히어로 헤드 | 24px | 44px |
| 페이지 타이틀 | 26px | 36px |
| 섹션 타이틀 | 20px | 26px |
| 카드 차량명 | 17px | 21px |
| 카드 가격 | 22px | 28px |
| 본문 | 14px | 15px |
| 메타/캡션 | 12px | 13px |

모든 헤딩에 `letter-spacing: -0.02em ~ -0.025em` 적용. 행간 `line-height: 1.2 ~ 1.25` (헤딩), `1.55 ~ 1.65` (본문).

### 3.3 스페이싱 & 라운드

```css
--radius-card: 20px;     /* 카드, 큰 영역 */
--radius-sm: 12px;       /* 인풋, 작은 박스 */
--radius-pill: 999px;    /* 칩, 버튼 */
```

어드민은 `--radius-card: 16px`로 살짝 작게 (정보 밀도 우선).

### 3.4 브레이크포인트

- < 768px: 모바일 (1열)
- 768 ~ 1023px: 태블릿 (2열)
- ≥ 1024px: PC (2열 슬라이더 또는 다열)
- ≥ 1280px: 초대형 (그대로 유지)

### 3.5 카드 그리드 규칙

**메인 페이지 차량 카드 (`차량 둘러보기`)**
- < 768px: **1열 세로** 스택
- 768 ~ 1023px: **2열 세로** 스택
- ≥ 1024px: **2열 × 2행 = 4대씩 한 페이지, 좌우 슬라이드**
  - `grid-template-rows: 1fr 1fr` + `grid-auto-flow: column`
  - `transform: translateX()` 로 페이지 이동
  - 화살표 버튼 + 페이지 인디케이터 (1/3 형식)
  - 키보드 방향키 지원

**업커밍 페이지**
- < 768px: 1열
- 768 ~ 1023px: 2열
- ≥ 1024px: 3열 (한 페이지 안에 모두 표시, 슬라이더 X)

**차량 상세 관련 차량**
- < 768px: 2열
- ≥ 1024px: 4열

### 3.6 카카오톡 통합 디자인 원칙

**플로팅 알약 버튼 (모든 공개 페이지)**
- 위치: 모바일 우하단 `bottom: 16px; right: 16px`, PC `bottom: 32px; right: 32px`
- 색: 노란색 `#FEE500` + 짙은 갈색 텍스트 `#3A1D1D`
- 모양: 알약형 (라운드 999px), 카카오 아이콘 + "1:1 문의" 텍스트
- 그림자: `0 6px 18px rgba(0,0,0,0.12)`

**예외**
- 차량 상세 모바일: 페이지 하단 고정 CTA 바가 있으므로 플로팅 숨김
- 어드민 (`/admin/*`): 플로팅 노출 안 함

---

## 4. 페이지별 상세 명세

### 4.1 메인 (`/`)

**섹션 구성**
1. **헤더** (sticky)
   - 로고 `GA:RAGE` (파란색 + 검정)
   - PC 메뉴: 홈 / 구독 / 렌트 / 슈퍼카 / 업커밍 / 고객센터
   - 우측: 언어 토글 (KR/ENG), MY 링크
2. **히어로 배너** (rerev 스타일)
   - 라운드 카드 배경 (--surface), 좌측 텍스트 + 우측 일러스트
   - 자동 롤링 (5초 간격, 페이드)
   - 우하단 카운터 `1/3`
   - 카피 예: "수리비 0원, 보증수리 무제한"
3. **빠른 진입 카드** (4개)
   - 모바일 2열 / PC 4열
   - 구독 vs 렌트 / 특가 차량 / 업커밍 / 고객센터
4. **차량 둘러보기**
   - 섹션 타이틀 + (PC: 슬라이더 화살표) + 추천순 셀렉트
   - 유형 탭: 전체 / 구독 / 렌트 / 슈퍼카 (밑줄 active)
   - 브랜드 가로 스크롤 (원형, 활성 시 파란 보더)
   - **차량 슬라이더 (위 3.5 규칙 따름)**
5. **푸터**

**차량 카드 구성**
- 모델명 + 배지 (구독/렌트/빠른출고/특가/NEW/SOLD)
- 가격 (`월 239만원 ~ 월 265만원` 형식)
- 메타 (`신차가 6,626만원 | 2025`)
- 차량 이미지 (drop-shadow로 떠 있는 느낌)
- 우상단 흐릿한 화살표 아이콘
- SOLD: 흑백 처리 + 가격 취소선

### 4.2 차량 상세 (`/vehicles/:id`)

1. 헤더 (공통) + 모바일 뒤로가기 / PC 브레드크럼
2. **갤러리** (모바일 풀폭, PC 라운드 16:10)
   - 좌우 화살표, 카운터 `01/12`, 하단 썸네일
3. **차량 헤더** — 브랜드(점+이름), 모델명+배지, 한 줄 소개, 큰 가격
4. **스펙 4분할 카드** — 연식 / 색상 / 연료 / 주행거리
5. **앵커 탭** (sticky) — 서비스 장점 / 비교 / 이용 절차 / FAQ
6. **서비스 장점** — 3열 카드 그리드, 체크 아이콘
7. **구독 vs 리스 vs 자차 비교 테이블** — 구독 컬럼이 파란색으로 강조, "추천" 배지
8. **이용 절차** — 4단계 카드 (카카오 문의 → 간편 심사 → 계약 → 인도)
9. **FAQ 아코디언** — 5~6개
10. **관련 차량** — 4열 카드 (작은 사이즈)
11. **PC 사이드 패널 (sticky)** — 가격 + 혜택 리스트 + 카카오 CTA + 찜
12. **모바일 하단 고정 CTA** — 가격 + 카카오 CTA + 찜 아이콘

### 4.3 업커밍 (`/upcoming`)

1. **페이지 히어로** — 보라+파랑 그라데이션 배경, "UPCOMING" 라벨, 통계 카드 3개 (1달 내 6대 / 준비 중 3대 / 다음 호 공개일)
2. **그룹 A — 1달 내 출고 가능**
   - 어드민 정렬 순서대로 카드 렌더링 (position ASC)
   - 각 카드에 ETA 라벨 (`12월 첫째 주 출고`, 파란색)
3. 그룹 사이 미니 디바이더 ("아직 컬렉션에 없는 차량")
4. **그룹 B — 그 밖에 준비 중**
   - 회색 톤 ETA (`2월 이후 출고 예정`)
5. **하단 CTA 배너** (검정 배경) — "출고 알림 신청하기" 카카오 CTA

### 4.4 고객센터 (`/faq`)

1. 페이지 타이틀
2. **2단 상단 그리드**
   - **카카오 카드** (검정 배경, 노란 액센트) — "전화·메일보다 훨씬 빠르게" + 운영시간 + 큰 카카오 버튼
   - **공지사항 리스트** (회색 카드) — 최근 5건, 필독 배지
3. **FAQ 섹션**
   - 카테고리 칩 (전체/가입/차량/구독/보험/점검/반납/기타) — 활성 시 검정
   - 아코디언 리스트 (회색 카드 배경) — 각 항목에 카테고리 라벨 + 질문 + 펼침 시 답변

### 4.5 로그인 · 회원가입 (`/login`, `/signup`)

1. **PC**: 좌측 비주얼 (큰 차량 사진 + 라이브 라벨 + 카피) / 우측 폼
2. **모바일**: 우측 폼만 전체 너비
3. **상단 미니 헤더** — 로고 + "홈으로" 링크
4. **세그먼트 탭** (회색 알약 컨테이너) — 로그인 / 회원가입
5. **카카오 버튼 우선** — 큰 노란 버튼 + 강조 힌트 ("3초만에 로그인")
6. **구분선** — "또는 이메일"
7. **폼 필드** — 회색 배경 인풋, 포커스 시 파란 보더
8. **회원가입**: 4개 필드 + **약관 동의 박스** (전체 + 개별 체크박스)

**카카오 OAuth 구현 가이드**
```
1. https://developers.kakao.com 앱 생성, Kakao 로그인 + Kakao Sync 활성화
2. 동의항목: 이메일(필수), 닉네임(필수), 휴대전화번호(선택)
3. Redirect URI: https://{domain}/auth/kakao/callback
4. Flask 라우트:
   - GET /auth/kakao → Kakao OAuth URL 리다이렉트
   - GET /auth/kakao/callback → code 받아 토큰 교환 → 사용자 정보 조회
                              → 기존 회원이면 로그인, 신규면 가입 처리
5. User 테이블에 kakao_id (Nullable, UNIQUE) 컬럼
```

### 4.6 어드민

#### 4.6.1 공통 레이아웃
- 좌측 사이드바 (240px) — 로고 + 메뉴 (대시보드 / 차량 목록 / 차량 등록 / 업커밍 순서 / 공지사항 / FAQ / 회원관리) + 사용자 정보
- 모바일은 사이드바 숨김 (햄버거 메뉴는 MVP 이후)
- 상단 toolbar — 브레드크럼 + 액션 버튼

#### 4.6.2 차량 등록 (`/admin/vehicles/new`)

**5개 필드 그룹**
1. **기본 정보** — 브랜드(select), 모델명, 트림, 연식, 색상, 주행거리, 연료, 변속, 신차가
2. **가격 · 노출 설정**
   - 월 구독료 최저가/최고가 (만원 단위)
   - 상품 유형 (구독/렌트/슈퍼카) — 알약 라디오
   - 공개 상태 (공개/숨김/SoldOut)
   - 표시 위치 (메인 컬렉션/업커밍 1달내/업커밍 그밖에/미배치)
   - 토글: 빠른 출고 배지 / 특가 차량 / 에디터스 픽
   - 예상 출고 라벨 (업커밍용)
3. **차량 이미지** — 드래그 드롭존 + 썸네일 그리드 (드래그 순서 변경, 대표 지정, 삭제)
4. **설명** — 한 줄 헤드라인 + 상세 설명 textarea
5. **편의 옵션** — 미리 정의된 12개 체크박스 (통풍시트, HUD, 하만카돈 등)

**Sticky form-actions** (하단 고정) — 자동저장 표시 + 임시저장 / 저장하기

#### 4.6.3 업커밍 순서 관리 (`/admin/upcoming/order`) — 핵심

**UX**
- 두 컬럼 (Group A "1달 내 출고" / Group B "그 밖에 준비 중")
- 각 컬럼에 차량 카드 리스트 (썸네일 + 모델명 + ETA + 위치번호 + 핸들 + 삭제)
- **SortableJS** 적용: 같은 컬럼 내 드래그 + 컬럼 간 드래그 모두 가능
- **자동 저장**: 드래그 종료 즉시 PATCH 요청, 우하단 토스트 노출
- 우상단 상시 표시: `자동 저장` 인디케이터 (초록 점 펄스)
- "차량 추가" 버튼 → 미배정 차량 목록 모달
- 카드 우측 × 버튼 → confirm → 업커밍에서 제외 (차량 자체 유지)

**API**
```
GET    /admin/api/upcoming/order
       → { group_a: [vehicle_ids in order], group_b: [vehicle_ids in order] }
PATCH  /admin/api/upcoming/order
       body: { group_a: [...], group_b: [...] }
       → 200 OK
```

---

## 5. 데이터 모델 (SQLAlchemy)

```python
class User(db.Model):
    id              = Column(Integer, primary_key=True)
    email           = Column(String(255), unique=True, nullable=True)
    password_hash   = Column(String(255), nullable=True)
    kakao_id        = Column(String(64), unique=True, nullable=True)
    name            = Column(String(60))
    phone           = Column(String(20))
    is_admin        = Column(Boolean, default=False)
    marketing_opt_in= Column(Boolean, default=False)
    created_at      = Column(DateTime, default=datetime.utcnow)


class Vehicle(db.Model):
    id              = Column(Integer, primary_key=True)
    brand           = Column(String(40), nullable=False)
    model           = Column(String(80), nullable=False)
    trim            = Column(String(80))
    year            = Column(Integer)
    color           = Column(String(40))
    fuel            = Column(String(20))      # 가솔린/디젤/하이브리드/전기/LPG
    transmission    = Column(String(20))      # 자동/수동
    mileage_km      = Column(Integer)
    plate           = Column(String(20))      # 내부용
    new_price_man   = Column(Integer)         # 신차가 (만원)
    headline        = Column(String(200))
    description     = Column(Text)
    options_json    = Column(JSON)
    
    # 상품 유형 및 가격
    product_type    = Column(Enum('subscription','rent','super'), default='subscription')
    price_min_man   = Column(Integer)         # 월 구독료 최저가 (만원)
    price_max_man   = Column(Integer)         # 최고가 (없으면 최저가만 노출)
    
    # 노출 제어
    visibility      = Column(Enum('public','hidden','soldout'), default='hidden')
    placement       = Column(Enum('collection','upcoming_a','upcoming_b','none'), default='none')
    is_featured     = Column(Boolean, default=False)   # 에디터스 픽
    is_fast         = Column(Boolean, default=False)   # 빠른 출고 배지
    is_deal         = Column(Boolean, default=False)   # 특가 배지
    eta_label       = Column(String(60))               # "12월 첫째 주 출고"
    
    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    images          = relationship('VehicleImage', backref='vehicle',
                                   order_by='VehicleImage.sort_order',
                                   cascade='all, delete-orphan')


class VehicleImage(db.Model):
    id          = Column(Integer, primary_key=True)
    vehicle_id  = Column(Integer, ForeignKey('vehicle.id', ondelete='CASCADE'))
    file_path   = Column(String(255), nullable=False)
    is_primary  = Column(Boolean, default=False)
    sort_order  = Column(Integer, default=0)


class UpcomingSlot(db.Model):
    """업커밍 순서 전용 테이블"""
    id          = Column(Integer, primary_key=True)
    vehicle_id  = Column(Integer, ForeignKey('vehicle.id', ondelete='CASCADE'), unique=True)
    group       = Column(Enum('a','b'), nullable=False)
    position    = Column(Integer, nullable=False)
    
    __table_args__ = (Index('ix_upcoming_group_position', 'group', 'position'),)


class Notice(db.Model):
    id          = Column(Integer, primary_key=True)
    title       = Column(String(200))
    body        = Column(Text)
    is_pinned   = Column(Boolean, default=False)
    is_visible  = Column(Boolean, default=True)
    created_at  = Column(DateTime, default=datetime.utcnow)


class FAQ(db.Model):
    id          = Column(Integer, primary_key=True)
    category    = Column(String(40))   # 가입/차량/구독/보험/점검/반납/기타
    question    = Column(String(300))
    answer      = Column(Text)
    sort_order  = Column(Integer, default=0)
    is_visible  = Column(Boolean, default=True)


class Favorite(db.Model):
    id          = Column(Integer, primary_key=True)
    user_id     = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'))
    vehicle_id  = Column(Integer, ForeignKey('vehicle.id', ondelete='CASCADE'))
    created_at  = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint('user_id', 'vehicle_id'),)


class Inquiry(db.Model):
    """카카오 이동 전 로깅 (선택)"""
    id          = Column(Integer, primary_key=True)
    user_id     = Column(Integer, ForeignKey('user.id'), nullable=True)
    vehicle_id  = Column(Integer, ForeignKey('vehicle.id'), nullable=True)
    source      = Column(String(40))     # 'detail_cta', 'floating', 'faq', 'upcoming'
    user_agent  = Column(String(255))
    created_at  = Column(DateTime, default=datetime.utcnow)


class SiteSetting(db.Model):
    """카카오채널 URL 등 환경설정"""
    key         = Column(String(60), primary_key=True)
    value       = Column(Text)
```

---

## 6. 공개 API 엔드포인트

| Method | Path | 설명 |
|---|---|---|
| GET | `/api/vehicles` | 메인 차량 목록 (쿼리: type, brand, sort) |
| GET | `/api/vehicles/:id` | 차량 상세 |
| GET | `/api/upcoming` | 업커밍 (그룹 a/b 분리, 어드민 순서대로) |
| GET | `/api/faq` | FAQ 목록 (?category=...) |
| GET | `/api/notices` | 공지사항 목록 |
| POST | `/api/favorites/:vehicle_id` | 찜 토글 (로그인 필요) |
| POST | `/api/inquiries` | 카카오 이동 전 로깅 (선택) |
| POST | `/api/auth/signup` | 일반 회원가입 |
| POST | `/api/auth/login` | 일반 로그인 |
| GET | `/auth/kakao` | 카카오 OAuth 시작 |
| GET | `/auth/kakao/callback` | 카카오 콜백 |
| POST | `/api/auth/logout` | 로그아웃 |

어드민 API:
| Method | Path | 설명 |
|---|---|---|
| POST | `/admin/api/vehicles` | 차량 등록 |
| PATCH | `/admin/api/vehicles/:id` | 수정 |
| DELETE | `/admin/api/vehicles/:id` | 삭제 |
| POST | `/admin/api/vehicles/:id/images` | 이미지 업로드 (multipart) |
| PATCH | `/admin/api/vehicles/:id/images/order` | 이미지 순서 변경 |
| PATCH | `/admin/api/upcoming/order` | **업커밍 순서 일괄 저장 (핵심)** |

---

## 7. 카카오톡 통합

**SiteSetting 키**
- `kakao_channel_url`: 예) `https://pf.kakao.com/_xxxxx/chat`
- `kakao_app_key`, `kakao_redirect_uri`: OAuth용

**플로팅 버튼 동작**
1. (선택) `POST /api/inquiries` 로 출처 로깅
2. `window.open(kakao_channel_url, '_blank')`

**노출 규칙**
- 모든 공개 페이지에 표시
- **차량 상세 모바일**: 페이지 하단 고정 CTA가 있어 플로팅 숨김
- 어드민 페이지 전 영역: 숨김

---

## 8. 디자인 초안 파일 매핑

| 파일명 | 페이지 | 비고 |
|---|---|---|
| `v4-index.html` | 메인 | PC 슬라이더 포함 |
| `v4-vehicle-detail.html` | 차량 상세 | PC 사이드 + 모바일 하단 CTA |
| `v4-upcoming.html` | 업커밍 | 두 그룹 |
| `v4-faq.html` | 고객센터 | 카카오 카드 + 공지 + FAQ |
| `v4-auth.html` | 로그인·회원가입 | 탭 전환 |
| `v4-admin-vehicle-new.html` | 차량 등록 | 5개 fieldset |
| `v4-admin-upcoming-order.html` | 업커밍 순서 관리 | SortableJS |

모든 파일은 단일 HTML에 인라인 CSS/JS. Claude Code는 디자인 토큰만 일관되게 유지하면서 React/Jinja2로 옮기면 됩니다. 토큰은 `static/css/tokens.css`로 추출 권장.

---

## 9. 개발 우선순위

**Sprint 1 — 기반 (1주)**
- Flask 초기화, DB 모델, 마이그레이션
- 디자인 토큰 추출, 공통 레이아웃 (헤더/푸터/플로팅 카카오)
- 메인 페이지 정적 구현 + 차량 슬라이더
- 차량 상세 정적 구현

**Sprint 2 — 어드민 (1주)**
- 어드민 인증 (`is_admin` flag)
- 차량 CRUD + 이미지 업로드
- 업커밍 순서 드래그앤드롭 (SortableJS)
- 공지사항 CRUD

**Sprint 3 — 사용자 (1주)**
- 회원가입/로그인 (일반)
- 카카오 OAuth (Kakao Sync)
- 마이페이지/찜
- 업커밍/FAQ 동적화

**Sprint 4 — 마감 (3~5일)**
- 카카오 채널 연결, 문의 로깅
- SEO 메타 태그, OG 이미지
- 반응형 QA
- 배포 (Gunicorn + Nginx)

---

## 10. 작업 시 주의사항 (Claude Code 인계)

- **결제 흐름 절대 추가하지 말 것**. 모든 전환은 카카오 채널로만.
- 차량 가격은 `price_min_man`만 있으면 `월 239만원`, 둘 다 있으면 `월 239만원 ~ 월 265만원` 형식.
- 어드민 업커밍 순서 저장은 **드래그 종료 즉시 PATCH**. 별도 저장 버튼 두지 말 것.
- 이미지 업로드는 처음에는 로컬 디스크로. 1GB 넘기면 R2/S3 마이그레이션.
- 카카오 OAuth 비즈앱 신청은 사업자 정보로 진행 필요 (전화번호 동의 항목).
- 모바일 플로팅 카카오 버튼은 차량 상세에서는 하단 고정 CTA와 겹치므로 숨김 처리.
- **PC 차량 슬라이더 작동 원리**:
  - `grid-template-rows: 1fr 1fr` + `grid-auto-flow: column`
  - 한 페이지 너비 = `container.clientWidth + 20px(gap)`
  - 카드 1·2가 첫 컬럼, 3·4가 두 번째 컬럼, ... 순서로 채워짐
  - 화면 리사이즈 시 재계산 (debounce 120ms)
- 디자인 토큰을 임의로 바꾸지 말 것. 한 가지만 어긋나도 톤이 깨짐.
- 어드민 사이드바는 모바일에서 숨김 (MVP 이후 햄버거 추가).
