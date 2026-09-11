import click
from flask import Flask

from app.extensions import db


def register_cli(app: Flask) -> None:
    @app.cli.command("create-admin")
    @click.option("--email", prompt=True)
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    @click.option("--name", default="Admin")
    def create_admin(email: str, password: str, name: str):
        """Create or promote an administrator account."""
        from app.models import User
        email = email.strip().lower()
        user = User.query.filter_by(email=email).first()
        if user is None:
            user = User(email=email, name=name, is_admin=True)
            user.set_password(password)
            db.session.add(user)
        else:
            user.is_admin = True
            user.set_password(password)
        db.session.commit()
        click.echo(f"OK admin user: {email}")

    @app.cli.command("seed-brands")
    def seed_brands():
        from app.models import Brand
        seeds = [
            ("BMW", "bmw"),
            ("Mercedes-Benz", "mercedes"),
            ("Audi", "audi"),
            ("Porsche", "porsche"),
            ("Genesis", "genesis"),
            ("Hyundai", "hyundai"),
            ("Kia", "kia"),
            ("Tesla", "tesla"),
            ("Land Rover", "land-rover"),
            ("Volvo", "volvo"),
        ]
        for i, (name, slug) in enumerate(seeds):
            existing = Brand.query.filter_by(slug=slug).first()
            logo = f"/static/img/brands/{slug}.svg"
            if existing is None:
                db.session.add(Brand(name=name, slug=slug, sort_order=i, logo_path=logo))
            elif not existing.logo_path:
                existing.logo_path = logo
        db.session.commit()
        click.echo(f"OK brands seeded: {Brand.query.count()}")

    @app.cli.command("seed-vehicles")
    def seed_vehicles():
        from app.models import Brand, Vehicle
        if Vehicle.query.count():
            click.echo("vehicles already present — skipping")
            return
        brand_by_slug = {b.slug: b for b in Brand.query.all()}
        required = ["bmw", "mercedes", "audi", "porsche", "genesis", "hyundai", "kia", "tesla", "land-rover", "volvo"]
        missing = [s for s in required if s not in brand_by_slug]
        if missing:
            click.echo(f"Run seed-brands first. Missing: {missing}")
            return

        # (model, brand_slug, year, color, pmin, pmax, new_price, fast, deal, feat, sold, placement)
        # placement: 'collection' | 'none' (none = will be assigned to upcoming slot later)
        items = [
            # === Main collection (placement='collection') — 12 vehicles ===
            ("5 Series 530i", "bmw", 2024, "그라파이트 그레이", 239, 265, 6626, True, True, False, False, "collection"),
            ("E-Class E250", "mercedes", 2024, "옵시디언 블랙", 269, 295, 7480, False, False, True, False, "collection"),
            ("G80", "genesis", 2024, "사빈 화이트", 159, 175, 6210, False, False, False, False, "collection"),
            ("Model 3 Long Range", "tesla", 2024, "퍼플", 89, 99, 5790, False, True, True, False, "collection"),
            ("X5 xDrive40i", "bmw", 2024, "알파인 화이트", 339, 379, 9890, False, False, False, True, "collection"),
            ("A6 45 TFSI", "audi", 2024, "데이토나 그레이", 219, 248, 7150, True, False, False, False, "collection"),
            ("GV70", "genesis", 2024, "마칼루 그레이", 189, 215, 6450, False, False, True, False, "collection"),
            ("Sorento 2.5T", "kia", 2024, "스노우 화이트 펄", 129, 149, 4980, True, True, False, False, "collection"),
            ("Range Rover Sport", "land-rover", 2024, "산토리니 블랙", 599, 690, 16800, False, False, True, False, "collection"),
            ("XC60 B5", "volvo", 2024, "크리스털 화이트", 169, 189, 6890, False, False, False, False, "collection"),
            ("3 Series 320i", "bmw", 2024, "미스티 블루", 169, 189, 5680, False, True, False, False, "collection"),
            ("Grandeur GN7", "hyundai", 2024, "팬텀 블랙", 109, 129, 4520, True, False, False, False, "collection"),

            # === Upcoming candidates (placement='none') — 20 vehicles, 10 per group ===
            # Group A intent (1달 내 구독) — set first
            ("Model Y Performance", "tesla", 2025, "딥 블루 메탈릭", 129, 149, 8290, True, False, True, False, "none"),
            ("Cayenne Coupe", "porsche", 2024, "어비스 그린", 690, 790, 19800, False, False, True, False, "none"),
            ("GV80 Coupe", "genesis", 2025, "카프리 블루", 249, 285, 9210, True, True, False, False, "none"),
            ("S-Class S500", "mercedes", 2024, "안트라사이트 블루", 599, 690, 19800, False, False, True, False, "none"),
            ("Q5 45 TFSI", "audi", 2024, "데일라잇 실버", 189, 219, 6890, False, True, False, False, "none"),
            ("EV9 Air", "kia", 2025, "글레이셔 화이트 펄", 169, 199, 7690, True, False, False, False, "none"),
            ("Stinger GT", "kia", 2025, "야로 옐로우", 159, 179, 5890, True, False, False, False, "none"),
            ("A4 40 TFSI", "audi", 2025, "글레이셔 화이트", 149, 169, 5180, False, True, False, False, "none"),
            ("C-Class C200", "mercedes", 2025, "스타링 블루", 199, 229, 6890, True, False, True, False, "none"),
            ("XC40 B4", "volvo", 2025, "퓨전 레드", 129, 149, 5290, False, False, False, False, "none"),

            # Group B intent (그 밖에 준비 중) — far ETA
            ("Taycan 4S", "porsche", 2025, "프로즌 베리", 790, 890, 22600, False, False, True, False, "none"),
            ("X7 xDrive40i", "bmw", 2025, "테니지 메탈릭", 449, 519, 14580, False, False, False, False, "none"),
            ("GLE 450", "mercedes", 2025, "셀레나이트 그레이", 349, 399, 11890, True, False, False, False, "none"),
            ("Defender 110", "land-rover", 2024, "팡고 옐로우", 419, 479, 12100, False, True, False, False, "none"),
            ("Ioniq 6", "hyundai", 2024, "트랜스미션 블루", 89, 109, 5290, False, False, True, False, "none"),
            ("EX90 Twin Motor", "volvo", 2025, "사파이어 블랙", 249, 289, 9890, True, False, False, False, "none"),
            ("718 Cayman", "porsche", 2025, "마이애미 블루", 490, 590, 14800, False, False, False, False, "none"),
            ("Q7 55 TFSI", "audi", 2025, "와이즈 그레이", 319, 359, 10890, False, False, True, False, "none"),
            ("M4 Competition", "bmw", 2025, "이졸데 블루", 599, 690, 16800, True, False, True, False, "none"),
            ("GV60 Performance", "genesis", 2025, "아드리아 블루", 199, 229, 7890, False, True, False, False, "none"),
        ]
        for model, slug, year, color, pmin, pmax, new_price, fast, deal, feat, sold, placement in items:
            v = Vehicle(
                brand_id=brand_by_slug[slug].id,
                model=model,
                year=year,
                color=color,
                fuel="gasoline",
                transmission="auto",
                mileage_km=10,
                new_price_man=new_price,
                price_min_man=pmin,
                price_max_man=pmax,
                product_type="subscription",
                visibility="soldout" if sold else "public",
                placement=placement,
                is_fast=fast,
                is_deal=deal,
                is_featured=feat,
                headline="수리비·보증 무제한, 24시간 전화 상담",
                description=(
                    "월 단위 구독으로 가볍게 시작하세요. 고객센터 전화 상담으로 모든 절차를 도와드립니다."
                ),
                options_json=["ventilated_seat", "heated_seat", "hud", "harman_kardon"],
            )
            db.session.add(v)
        db.session.commit()
        click.echo(f"OK vehicles seeded: {Vehicle.query.count()}")

    @app.cli.command("seed-upcoming")
    def seed_upcoming():
        from app.models import Vehicle, UpcomingSlot
        if UpcomingSlot.query.count():
            click.echo("upcoming slots already present — skipping")
            return
        candidates = (
            Vehicle.query.filter_by(placement="none")
            .order_by(Vehicle.id.asc())
            .all()
        )
        if len(candidates) < 10:
            click.echo(f"Need at least 10 upcoming-candidate vehicles, have {len(candidates)}. Run seed-vehicles first.")
            return
        group_a_etas = [
            "12월 첫째 주 구독 가능",
            "12월 둘째 주 구독 가능",
            "12월 셋째 주 구독 가능",
            "12월 넷째 주 구독 가능",
            "1월 첫째 주 구독 가능",
            "1월 둘째 주 구독 가능",
            "1월 셋째 주 구독 가능",
            "1월 넷째 주 구독 가능",
            "2월 첫째 주 구독 가능",
            "2월 둘째 주 구독 가능",
        ]
        group_b_etas = [
            "2월 이후 출고 예정",
            "2월 이후 출고 예정",
            "3월 이후 출고 예정",
            "3월 이후 출고 예정",
            "4월 이후 출고 예정",
            "4월 이후 출고 예정",
            "5월 이후 출고 예정",
            "5월 이후 출고 예정",
            "6월 이후 출고 예정",
            "6월 이후 출고 예정",
        ]
        a_pool = candidates[:10]
        b_pool = candidates[10:20]
        for i, v in enumerate(a_pool):
            db.session.add(UpcomingSlot(vehicle_id=v.id, group="a", position=i))
            v.eta_label = group_a_etas[i] if i < len(group_a_etas) else group_a_etas[-1]
        for i, v in enumerate(b_pool):
            db.session.add(UpcomingSlot(vehicle_id=v.id, group="b", position=i))
            v.eta_label = group_b_etas[i] if i < len(group_b_etas) else group_b_etas[-1]
        db.session.commit()
        click.echo(f"OK upcoming seeded: A={len(a_pool)}, B={len(b_pool)}")

    @app.cli.command("seed-faq")
    def seed_faq():
        from app.models import FAQ
        if FAQ.query.count():
            click.echo("faq already present — skipping")
            return
        items = [
            ("signup", "회원가입은 어떻게 하나요?",
             "카카오톡으로 3초 만에 가입할 수 있습니다. 일반 이메일 가입도 지원합니다."),
            ("vehicle", "차량은 직접 보러 갈 수 있나요?",
             "고객센터 전화 또는 1:1 문의를 남겨주시면 시승 일정을 조율해드립니다."),
            ("subscription", "구독 vs 렌트 차이가 뭔가요?",
             "구독은 보증·정비·세금이 모두 포함된 풀패키지, 렌트는 단기 위주입니다."),
            ("insurance", "보험은 별도 가입인가요?",
             "월 구독료에 종합 보험이 포함되어 있습니다."),
            ("inspection", "정기 점검은 어떻게 진행되나요?",
             "전국 인증 정비망에서 무상으로 진행됩니다."),
            ("return", "반납할 때 위약금이 있나요?",
             "약정 기간에 따라 다릅니다. 자세한 사항은 고객센터 전화 상담으로 안내드립니다."),
        ]
        for i, (cat, q, a) in enumerate(items):
            db.session.add(FAQ(category=cat, question=q, answer=a, sort_order=i))
        db.session.commit()
        click.echo(f"OK faq seeded: {FAQ.query.count()}")

    @app.cli.command("seed-banners")
    def seed_banners():
        from app.models import Banner
        if Banner.query.count():
            click.echo("banners already present — skipping")
            return
        # 기본 배너 3개 (image_path 없이 — 어드민이 필요 시 이미지 URL 추가)
        defaults = [
            ("FOR SUBSCRIBERS", "수리비 0원,\n보증수리 무제한",
             "차량 한 대를 한 달 단위로 가볍게 시작하세요.\n24시간 전화 상담.", None, 0),
            ("NEW ARRIVALS", "이번 달의\n업커밍 차량 공개",
             "에디터가 큐레이션한 다음 차례의 차량들. 전화·1:1 문의로 가장 먼저 안내드립니다.", "/upcoming", 1),
            ("24H SUPPORT", "언제든 전화 한 통으로\n빠르게",
             "24시간 상담 가능. 시승·계약·상담 모두 전화 한 통으로.", None, 2),
        ]
        for eyebrow, title, subtitle, link, order in defaults:
            db.session.add(Banner(
                eyebrow=eyebrow, title=title, subtitle=subtitle,
                link_url=link, sort_order=order, is_visible=True,
                image_path=None,
            ))
        db.session.commit()
        click.echo(
            f"OK banners seeded: {Banner.query.count()} (텍스트만 — 이미지는 어드민에서 업로드하세요)"
        )

    @app.cli.command("seed-real")
    def seed_real():
        """Wipe vehicle data and insert 3 realistic vehicles with generated images."""
        import uuid
        from pathlib import Path
        from app.models import Brand, Vehicle, VehicleImage, UpcomingSlot, Favorite, Inquiry
        from flask import current_app

        # Wipe
        Favorite.query.delete()
        Inquiry.query.delete()
        UpcomingSlot.query.delete()
        VehicleImage.query.delete()
        Vehicle.query.delete()
        db.session.commit()

        brand_by_slug = {b.slug: b for b in Brand.query.all()}
        needed = ("bmw", "mercedes", "genesis")
        missing = [s for s in needed if s not in brand_by_slug]
        if missing:
            click.echo(f"Missing brands: {missing}. Run seed-brands first.")
            return

        specs = [
            {
                "brand_slug": "bmw",
                "model": "5 Series 530i M Sport",
                "trim_year_caption": "M Sport · 2024",
                "year": 2024,
                "color": "알파인 화이트",
                "mileage_km": 12,
                "new_price_man": 6626,
                "price_min_man": 239,
                "price_max_man": 265,
                "headline": "수리비 0원, 보증수리 무제한 · 프리미엄 세단의 정석",
                "description": (
                    "BMW 5 Series 530i M Sport — 다이내믹 주행과 세련된 디자인.\n\n"
                    "· 2.0L 트윈파워 터보 (최고출력 252마력)\n"
                    "· ZF 8단 스텝트로닉\n"
                    "· 어댑티브 M 서스펜션, 라이브 콕핏 프로페셔널\n"
                    "· 하만카돈 서라운드, HUD, 어라운드뷰\n\n"
                    "고객센터 전화 상담으로 시승·계약을 도와드립니다."
                ),
                "is_featured": True,
                "is_fast": True,
                "is_deal": False,
                "options": ["ventilated_seat", "heated_seat", "hud", "harman_kardon", "adaptive_cruise", "lane_assist"],
                "img_color": (52, 82, 163),  # BMW blue
            },
            {
                "brand_slug": "mercedes",
                "model": "E-Class E 250 Avantgarde",
                "trim_year_caption": "Avantgarde · 2024",
                "year": 2024,
                "color": "옵시디언 블랙",
                "mileage_km": 8,
                "new_price_man": 7480,
                "price_min_man": 269,
                "price_max_man": 295,
                "headline": "럭셔리 세단의 새로운 기준 · MBUX 슈퍼스크린 탑재",
                "description": (
                    "Mercedes-Benz E 250 Avantgarde — 편안함과 첨단 인포테인먼트.\n\n"
                    "· 2.0L 가솔린 (최고출력 258마력)\n"
                    "· 9G-Tronic 자동변속기\n"
                    "· MBUX 슈퍼스크린, 파노라마 루프\n"
                    "· 부메스터 3D 사운드, 어라운드뷰, HUD\n\n"
                    "월 269만원부터 · 24시간 전화 상담."
                ),
                "is_featured": True,
                "is_fast": False,
                "is_deal": False,
                "options": ["ventilated_seat", "heated_seat", "hud", "surround_view", "adaptive_cruise", "panoramic_roof"],
                "img_color": (33, 33, 43),  # Merc dark
            },
            {
                "brand_slug": "genesis",
                "model": "G80 2.5T AWD Prestige",
                "trim_year_caption": "Prestige · 2024",
                "year": 2024,
                "color": "사빈 화이트",
                "mileage_km": 15,
                "new_price_man": 6210,
                "price_min_man": 159,
                "price_max_man": 175,
                "headline": "한국 럭셔리의 자부심 · 편안함과 정숙성의 조화",
                "description": (
                    "Genesis G80 2.5T AWD Prestige — 정숙성과 편의성을 갖춘 K-럭셔리.\n\n"
                    "· 2.5L 가솔린 터보 (최고출력 304마력)\n"
                    "· 8단 자동변속기, 전자식 상시 사륜구동\n"
                    "· 렉시콘 사운드, 나파 가죽 시트\n"
                    "· 원격 스마트 주차, 어라운드뷰, HUD\n\n"
                    "월 159만원부터 · 빠른 출고 가능."
                ),
                "is_featured": False,
                "is_fast": True,
                "is_deal": True,
                "options": ["ventilated_seat", "heated_seat", "hud", "surround_view", "lane_assist", "auto_parking"],
                "img_color": (17, 45, 78),  # Genesis navy
            },
        ]

        # === Upcoming intent — placement='none', assigned to UpcomingSlot ===
        # (group_letter, position, eta_label) + same shape as `specs`
        upcoming_specs = [
            # Group A (1달 내 구독 가능)
            ("a", 0, "12월 첫째 주 구독 가능", {
                "brand_slug": "tesla",
                "model": "Model Y Performance",
                "trim_year_caption": "Performance · 2025",
                "year": 2025, "color": "딥 블루 메탈릭",
                "mileage_km": 5, "new_price_man": 8290,
                "price_min_man": 129, "price_max_man": 149,
                "headline": "고성능 전기 SUV · 즉시 인도 가능",
                "description": "Tesla Model Y Performance — 3.7초 제로백, 오토파일럿 기본.\n\n· 듀얼 모터 AWD\n· 완충 시 최대 514km 주행\n· 20인치 유벨딕 휠",
                "is_featured": True, "is_fast": False, "is_deal": True,
                "options": ["heated_seat", "adaptive_cruise", "lane_assist", "auto_parking"],
                "img_color": (18, 32, 56),
            }),
            ("a", 1, "12월 둘째 주 구독 가능", {
                "brand_slug": "porsche",
                "model": "Cayenne Coupe",
                "trim_year_caption": "Coupe · 2024",
                "year": 2024, "color": "어비스 그린",
                "mileage_km": 3, "new_price_man": 19800,
                "price_min_man": 690, "price_max_man": 790,
                "headline": "쿠페 실루엣의 럭셔리 SUV",
                "description": "Porsche Cayenne Coupe — 강렬한 성능과 실용성.\n\n· 3.0L V6 터보\n· PDK 8단 자동\n· BOSE 사운드, 파노라마 루프",
                "is_featured": True, "is_fast": False, "is_deal": False,
                "options": ["ventilated_seat", "heated_seat", "surround_view", "panoramic_roof"],
                "img_color": (32, 56, 44),
            }),
            ("a", 2, "12월 셋째 주 구독 가능", {
                "brand_slug": "genesis",
                "model": "GV80 Coupe Signature",
                "trim_year_caption": "Signature · 2025",
                "year": 2025, "color": "카프리 블루",
                "mileage_km": 2, "new_price_man": 9210,
                "price_min_man": 249, "price_max_man": 285,
                "headline": "쿠페 SUV의 새로운 기준",
                "description": "Genesis GV80 Coupe — 다이내믹 실루엣과 K-럭셔리.\n\n· 3.5L V6 가솔린 터보\n· 8단 자동변속기\n· 렉시콘 사운드, HUD, 어라운드뷰",
                "is_featured": True, "is_fast": True, "is_deal": False,
                "options": ["ventilated_seat", "heated_seat", "hud", "surround_view", "adaptive_cruise"],
                "img_color": (30, 60, 100),
            }),
            # Group B (그 밖에 준비 중)
            ("b", 0, "2월 이후 출고 예정", {
                "brand_slug": "porsche",
                "model": "Taycan 4S",
                "trim_year_caption": "4S · 2025",
                "year": 2025, "color": "프로즌 베리 메탈릭",
                "mileage_km": 0, "new_price_man": 22600,
                "price_min_man": 790, "price_max_man": 890,
                "headline": "전기 스포츠 세단의 정점",
                "description": "Porsche Taycan 4S — 극한 성능과 럭셔리를 겸비한 전기 스포츠 세단.\n\n· 듀얼 모터 AWD, 최고출력 490마력\n· 800V 급속 충전\n· 21인치 마이애미 휠",
                "is_featured": True, "is_fast": False, "is_deal": False,
                "options": ["ventilated_seat", "heated_seat", "hud", "adaptive_cruise"],
                "img_color": (100, 30, 60),
            }),
            ("b", 1, "3월 이후 출고 예정", {
                "brand_slug": "bmw",
                "model": "X7 xDrive40i M Sport",
                "trim_year_caption": "M Sport · 2025",
                "year": 2025, "color": "테니지 메탈릭",
                "mileage_km": 0, "new_price_man": 14580,
                "price_min_man": 449, "price_max_man": 519,
                "headline": "플래그십 럭셔리 SUV",
                "description": "BMW X7 xDrive40i — 강렬한 존재감과 최상급 편의성.\n\n· 3.0L 직렬6 터보\n· 8단 스텝트로닉, xDrive\n· 하만카돈, 파노라마 스카이 라운지",
                "is_featured": False, "is_fast": False, "is_deal": False,
                "options": ["ventilated_seat", "heated_seat", "hud", "harman_kardon", "panoramic_roof"],
                "img_color": (52, 82, 163),
            }),
            ("b", 2, "3월 이후 출고 예정", {
                "brand_slug": "land-rover",
                "model": "Defender 110 P400e",
                "trim_year_caption": "P400e · 2024",
                "year": 2024, "color": "팡고 옐로우",
                "mileage_km": 0, "new_price_man": 12100,
                "price_min_man": 419, "price_max_man": 479,
                "headline": "오프로드의 상징 · 정통 SUV",
                "description": "Land Rover Defender 110 P400e — 어떤 지형도 정복하는 아이코닉 SUV.\n\n· 2.0L 플러그인 하이브리드\n· 지형 반응 시스템\n· 메리디언 사운드",
                "is_featured": False, "is_fast": False, "is_deal": True,
                "options": ["heated_seat", "surround_view", "lane_assist", "auto_parking"],
                "img_color": (204, 158, 45),
            }),
        ]

        # Insert collection vehicles
        created = []
        for spec in specs:
            v = Vehicle(
                brand_id=brand_by_slug[spec["brand_slug"]].id,
                model=spec["model"],
                year=spec["year"],
                color=spec["color"],
                fuel="gasoline",
                transmission="auto",
                mileage_km=spec["mileage_km"],
                new_price_man=spec["new_price_man"],
                price_min_man=spec["price_min_man"],
                price_max_man=spec["price_max_man"],
                product_type="subscription",
                visibility="public",
                placement="collection",
                is_featured=spec["is_featured"],
                is_fast=spec["is_fast"],
                is_deal=spec["is_deal"],
                headline=spec["headline"],
                description=spec["description"],
                options_json=spec["options"],
            )
            db.session.add(v)
            created.append((v, spec))

        # Insert upcoming vehicles
        upcoming_created = []
        for group, pos, eta, uspec in upcoming_specs:
            v = Vehicle(
                brand_id=brand_by_slug[uspec["brand_slug"]].id,
                model=uspec["model"],
                year=uspec["year"],
                color=uspec["color"],
                fuel="gasoline",
                transmission="auto",
                mileage_km=uspec["mileage_km"],
                new_price_man=uspec["new_price_man"],
                price_min_man=uspec["price_min_man"],
                price_max_man=uspec["price_max_man"],
                product_type="subscription",
                visibility="public",
                placement="none",
                is_featured=uspec["is_featured"],
                is_fast=uspec["is_fast"],
                is_deal=uspec["is_deal"],
                headline=uspec["headline"],
                description=uspec["description"],
                options_json=uspec["options"],
                eta_label=eta,
            )
            db.session.add(v)
            upcoming_created.append((v, uspec, group, pos))
        db.session.commit()

        # Attach UpcomingSlot rows
        for v, uspec, group, pos in upcoming_created:
            db.session.add(UpcomingSlot(vehicle_id=v.id, group=group, position=pos))
        db.session.commit()

        click.echo(
            f"OK real seed: {len(created)} collection + {len(upcoming_created)} upcoming"
            f" (no auto-generated images; upload real photos via admin)"
        )

    @app.cli.command("seed-all")
    @click.pass_context
    def seed_all(ctx):
        ctx.invoke(seed_brands)
        ctx.invoke(seed_vehicles)
        ctx.invoke(seed_upcoming)
        ctx.invoke(seed_faq)
        ctx.invoke(seed_banners)


