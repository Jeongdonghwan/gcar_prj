from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    IntegerField,
    SelectField,
    SelectMultipleField,
    StringField,
    TextAreaField,
    widgets,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional, Regexp

from app.models.vehicle import FUEL_TYPES, PRODUCT_TYPES, TRANSMISSION_TYPES, VISIBILITY_STATES
from app.models.content import FAQ_CATEGORIES


# === Korean labels for enum-style fields ===
FUEL_LABELS = {
    "gasoline": "가솔린",
    "diesel": "디젤",
    "hybrid": "하이브리드",
    "ev": "전기",
    "lpg": "LPG",
}
TRANSMISSION_LABELS = {"auto": "자동", "manual": "수동"}
PRODUCT_TYPE_LABELS = {
    "subscription": "구독",
    "rent": "렌트",
    "super": "슈퍼카",
}
VISIBILITY_LABELS = {
    "public": "공개",
    "hidden": "숨김",
    "soldout": "판매완료 (Sold Out)",
}
FAQ_CATEGORY_LABELS = {
    "signup": "가입",
    "vehicle": "차량",
    "subscription": "구독",
    "insurance": "보험",
    "inspection": "점검",
    "return": "반납",
    "etc": "기타",
}


COMFORT_OPTIONS = [
    ("ventilated_seat", "통풍시트"),
    ("heated_seat", "열선시트"),
    ("hud", "HUD"),
    ("surround_view", "어라운드뷰"),
    ("harman_kardon", "하만카돈"),
    ("sunroof", "선루프"),
    ("panoramic_roof", "파노라마 루프"),
    ("apple_carplay", "Apple CarPlay"),
    ("android_auto", "Android Auto"),
    ("adaptive_cruise", "어댑티브 크루즈"),
    ("lane_assist", "차선 유지 보조"),
    ("auto_parking", "자동 주차"),
]


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class VehicleForm(FlaskForm):
    # 1) 기본 정보
    brand_id = SelectField("브랜드", coerce=int, validators=[DataRequired()])
    model = StringField("모델명 (트림 포함)", validators=[DataRequired(), Length(max=80)])
    year = IntegerField("연식", validators=[DataRequired(), NumberRange(min=1980, max=2100)])
    color = StringField("색상", validators=[Optional(), Length(max=40)])
    mileage_km = IntegerField("주행거리(km)", validators=[Optional(), NumberRange(min=0)])
    fuel = SelectField("연료", choices=[(v, FUEL_LABELS.get(v, v)) for v in FUEL_TYPES])
    transmission = SelectField("변속", choices=[(v, TRANSMISSION_LABELS.get(v, v)) for v in TRANSMISSION_TYPES])
    plate = StringField("번호판(내부용)", validators=[Optional(), Length(max=20)])

    # 2) 가격·노출
    price_min_man = IntegerField("월 구독료 최저가(만원)", validators=[Optional(), NumberRange(min=0)])
    price_max_man = IntegerField("월 구독료 최고가(만원)", validators=[Optional(), NumberRange(min=0)])
    product_type = SelectField("상품 유형", choices=[(v, PRODUCT_TYPE_LABELS.get(v, v)) for v in PRODUCT_TYPES], default="subscription")
    visibility = SelectField("공개 상태", choices=[(v, VISIBILITY_LABELS.get(v, v)) for v in VISIBILITY_STATES], default="public")
    show_in_collection = BooleanField("메인 컬렉션 노출")
    upcoming_group = SelectField(
        "업커밍 배치",
        choices=[("none", "미배치"), ("a", "그룹 A — 1달 내"), ("b", "그룹 B — 그 밖에")],
        default="none",
    )
    is_fast = BooleanField("빠른 출고 배지")
    is_deal = BooleanField("특가 차량")
    is_featured = BooleanField("에디터스 픽")
    eta_label = StringField("예상 출고 라벨", validators=[Optional(), Length(max=60)])

    # 4) 설명
    headline = StringField("한 줄 헤드라인", validators=[Optional(), Length(max=200)])
    description = TextAreaField("상세 설명", validators=[Optional()])

    # 5) 편의 옵션
    options = MultiCheckboxField("편의 옵션", choices=COMFORT_OPTIONS)


class NoticeForm(FlaskForm):
    title = StringField("제목", validators=[DataRequired(), Length(max=200)])
    body = TextAreaField("본문 (Markdown)", validators=[DataRequired()])
    is_pinned = BooleanField("상단 고정")
    is_visible = BooleanField("공개", default=True)


class FAQForm(FlaskForm):
    category = SelectField("카테고리", choices=[(c, FAQ_CATEGORY_LABELS.get(c, c)) for c in FAQ_CATEGORIES])
    question = StringField("질문", validators=[DataRequired(), Length(max=300)])
    answer = TextAreaField("답변", validators=[DataRequired()])
    sort_order = IntegerField("정렬 순서", default=0)
    is_visible = BooleanField("공개", default=True)


class BrandForm(FlaskForm):
    name = StringField("브랜드명", validators=[DataRequired(), Length(max=40)])
    slug = StringField(
        "슬러그 (URL용)",
        validators=[
            DataRequired(),
            Length(max=40),
            Regexp(r"^[a-z0-9\-]+$", message="소문자·숫자·하이픈만 허용됩니다."),
        ],
    )
    sort_order = IntegerField("정렬 순서", default=0)
    is_visible = BooleanField("공개", default=True)


class BannerForm(FlaskForm):
    # 텍스트 필드는 하위호환용으로 스키마에 유지 (fallback 다크 배너에서 사용),
    # 어드민 UI에서는 숨김. title은 서버측 자동 기본값으로 처리.
    eyebrow = StringField("상단 라벨", validators=[Optional(), Length(max=60)])
    title = StringField("타이틀", validators=[Optional(), Length(max=120)])
    subtitle = StringField("서브 카피", validators=[Optional(), Length(max=200)])
    link_url = StringField("연결 URL (선택)", validators=[Optional(), Length(max=255)])
    sort_order = IntegerField("정렬 순서", default=0)
    is_visible = BooleanField("공개", default=True)
