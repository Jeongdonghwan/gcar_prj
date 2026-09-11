from datetime import datetime
from pathlib import Path
from flask import flash, redirect, render_template, request, url_for

from app.extensions import db
from app.forms.vehicle_forms import (
    BannerForm,
    BrandForm,
    FAQForm,
    NoticeForm,
    QnaAnswerForm,
    VehicleForm,
)
from app.models import Banner, Brand, FAQ, Notice, QnaPost, UpcomingSlot, User, Vehicle
from app.models.vehicle import VISIBILITY_STATES
from app.services import upcoming_service
from app.services.site_settings import (
    get_contact_hours,
    get_contact_phone,
    set_value as set_site_setting,
)
from . import admin_bp


@admin_bp.route("/")
def dashboard():
    counts = {
        "vehicles": Vehicle.query.count(),
        "vehicles_public": Vehicle.query.filter_by(visibility="public").count(),
        "upcoming": UpcomingSlot.query.count(),
        "users": User.query.filter_by(deleted_at=None).count(),
        "notices": Notice.query.count(),
    }
    recent = Vehicle.query.order_by(Vehicle.created_at.desc()).limit(8).all()
    return render_template("admin/dashboard.html", counts=counts, recent=recent)


# --- Vehicles ---------------------------------------------------------------
@admin_bp.route("/vehicles")
def vehicles():
    q = Vehicle.query.order_by(Vehicle.created_at.desc()).all()
    return render_template("admin/vehicles.html", vehicles=q)


@admin_bp.route("/vehicles/new", methods=["GET", "POST"])
def vehicles_new():
    form = _build_vehicle_form()
    if form.validate_on_submit():
        v = Vehicle()
        _apply_vehicle_form(v, form)
        db.session.add(v)
        db.session.commit()
        _sync_upcoming_after_save(v, form.upcoming_group.data)
        flash("차량이 등록되었습니다. 이어서 이미지를 업로드하세요.", "success")
        return redirect(url_for("admin.vehicles_edit", vehicle_id=v.id))
    return render_template("admin/vehicle_form.html", form=form, vehicle=None)


@admin_bp.route("/vehicles/<int:vehicle_id>/edit", methods=["GET", "POST"])
def vehicles_edit(vehicle_id: int):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    form = _build_vehicle_form(vehicle)
    if form.validate_on_submit():
        _apply_vehicle_form(vehicle, form)
        db.session.commit()
        _sync_upcoming_after_save(vehicle, form.upcoming_group.data)
        flash("저장되었습니다.", "success")
        return redirect(url_for("admin.vehicles_edit", vehicle_id=vehicle.id))
    return render_template("admin/vehicle_form.html", form=form, vehicle=vehicle)


@admin_bp.route("/vehicles/<int:vehicle_id>/delete", methods=["POST"])
def vehicles_delete(vehicle_id: int):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    from app.services.image_service import remove_vehicle_dir
    remove_vehicle_dir(vehicle_id)
    db.session.delete(vehicle)
    db.session.commit()
    flash("차량이 삭제되었습니다.", "success")
    return redirect(url_for("admin.vehicles"))


VISIBILITY_LABELS = {"public": "공개", "hidden": "숨김", "soldout": "판매완료"}


@admin_bp.route("/vehicles/<int:vehicle_id>/visibility", methods=["POST"])
def vehicles_set_visibility(vehicle_id: int):
    v = Vehicle.query.get_or_404(vehicle_id)
    new_state = (request.form.get("visibility") or "").strip()
    if new_state not in VISIBILITY_STATES:
        flash("잘못된 상태 값입니다.", "error")
    elif v.visibility == new_state:
        flash(f"'{v.model}'은(는) 이미 '{VISIBILITY_LABELS[new_state]}' 상태입니다.", "info")
    else:
        v.visibility = new_state
        db.session.commit()
        flash(f"'{v.model}' 상태를 '{VISIBILITY_LABELS[new_state]}'(으)로 변경했습니다.", "success")
    return redirect(url_for("admin.vehicles"))


def _build_vehicle_form(vehicle: Vehicle | None = None) -> VehicleForm:
    form = VehicleForm(obj=vehicle)
    form.brand_id.choices = [(b.id, b.name) for b in Brand.query.order_by(Brand.sort_order).all()]
    if vehicle is not None:
        form.show_in_collection.data = vehicle.placement == "collection"
        slot = vehicle.upcoming_slot
        form.upcoming_group.data = slot.group if slot else "none"
        form.options.data = list(vehicle.options_json or [])
    return form


def _apply_vehicle_form(v: Vehicle, form: VehicleForm) -> None:
    v.brand_id = form.brand_id.data
    v.model = form.model.data
    v.year = form.year.data
    v.color = form.color.data or None
    v.mileage_km = form.mileage_km.data
    v.fuel = form.fuel.data
    v.transmission = form.transmission.data
    v.plate = form.plate.data or None
    v.price_min_man = form.price_min_man.data
    v.price_max_man = form.price_max_man.data
    v.price_3m_man = form.price_3m_man.data
    v.price_6m_man = form.price_6m_man.data
    v.price_24m_man = form.price_24m_man.data
    v.deposit_man = form.deposit_man.data
    v.prepay_man = form.prepay_man.data
    v.product_type = form.product_type.data
    v.visibility = form.visibility.data
    v.placement = "collection" if form.show_in_collection.data else "none"
    v.is_fast = form.is_fast.data
    v.is_deal = form.is_deal.data
    v.is_featured = form.is_featured.data
    v.eta_label = form.eta_label.data or None
    v.headline = form.headline.data or None
    v.description = form.description.data or None
    v.options_json = list(form.options.data or [])


def _sync_upcoming_after_save(v: Vehicle, group: str) -> None:
    if group in ("a", "b"):
        upcoming_service.add_to_group(v.id, group)
    else:
        upcoming_service.remove(v.id)


# --- Upcoming order ---------------------------------------------------------
@admin_bp.route("/upcoming/order")
def upcoming_order():
    order = upcoming_service.get_order()
    a_vehicles = (
        Vehicle.query.filter(Vehicle.id.in_(order["group_a"])).all()
        if order["group_a"] else []
    )
    b_vehicles = (
        Vehicle.query.filter(Vehicle.id.in_(order["group_b"])).all()
        if order["group_b"] else []
    )
    # Preserve order
    def _ordered(ids, items):
        m = {x.id: x for x in items}
        return [m[i] for i in ids if i in m]
    return render_template(
        "admin/upcoming_order.html",
        group_a=_ordered(order["group_a"], a_vehicles),
        group_b=_ordered(order["group_b"], b_vehicles),
        unassigned=upcoming_service.unassigned_vehicles(),
    )


# --- Notices ----------------------------------------------------------------
@admin_bp.route("/notices")
def notices():
    items = Notice.query.order_by(Notice.is_pinned.desc(), Notice.created_at.desc()).all()
    return render_template("admin/notices.html", notices=items)


@admin_bp.route("/notices/new", methods=["GET", "POST"])
def notices_new():
    form = NoticeForm()
    if form.validate_on_submit():
        n = Notice(
            title=form.title.data,
            body=form.body.data,
            is_pinned=form.is_pinned.data,
            is_visible=form.is_visible.data,
        )
        db.session.add(n)
        db.session.commit()
        flash("공지가 등록되었습니다.", "success")
        return redirect(url_for("admin.notices"))
    return render_template("admin/notice_form.html", form=form, notice=None)


@admin_bp.route("/notices/<int:notice_id>/edit", methods=["GET", "POST"])
def notices_edit(notice_id: int):
    n = Notice.query.get_or_404(notice_id)
    form = NoticeForm(obj=n)
    if form.validate_on_submit():
        n.title = form.title.data
        n.body = form.body.data
        n.is_pinned = form.is_pinned.data
        n.is_visible = form.is_visible.data
        db.session.commit()
        flash("저장되었습니다.", "success")
        return redirect(url_for("admin.notices"))
    return render_template("admin/notice_form.html", form=form, notice=n)


@admin_bp.route("/notices/<int:notice_id>/delete", methods=["POST"])
def notices_delete(notice_id: int):
    n = Notice.query.get_or_404(notice_id)
    db.session.delete(n)
    db.session.commit()
    return redirect(url_for("admin.notices"))


# --- FAQ -------------------------------------------------------------------
@admin_bp.route("/faq")
def faq_list():
    items = FAQ.query.order_by(FAQ.category.asc(), FAQ.sort_order.asc()).all()
    return render_template("admin/faq_list.html", faqs=items)


@admin_bp.route("/faq/new", methods=["GET", "POST"])
def faq_new():
    form = FAQForm()
    if form.validate_on_submit():
        f = FAQ(
            category=form.category.data,
            question=form.question.data,
            answer=form.answer.data,
            sort_order=form.sort_order.data or 0,
            is_visible=form.is_visible.data,
        )
        db.session.add(f)
        db.session.commit()
        return redirect(url_for("admin.faq_list"))
    return render_template("admin/faq_form.html", form=form, faq=None)


@admin_bp.route("/faq/<int:faq_id>/edit", methods=["GET", "POST"])
def faq_edit(faq_id: int):
    f = FAQ.query.get_or_404(faq_id)
    form = FAQForm(obj=f)
    if form.validate_on_submit():
        f.category = form.category.data
        f.question = form.question.data
        f.answer = form.answer.data
        f.sort_order = form.sort_order.data or 0
        f.is_visible = form.is_visible.data
        db.session.commit()
        return redirect(url_for("admin.faq_list"))
    return render_template("admin/faq_form.html", form=form, faq=f)


@admin_bp.route("/faq/<int:faq_id>/delete", methods=["POST"])
def faq_delete(faq_id: int):
    f = FAQ.query.get_or_404(faq_id)
    db.session.delete(f)
    db.session.commit()
    return redirect(url_for("admin.faq_list"))


# --- Brands ---------------------------------------------------------------
@admin_bp.route("/brands")
def brands():
    items = Brand.query.order_by(Brand.sort_order.asc(), Brand.id.asc()).all()
    return render_template("admin/brands.html", brands=items)


@admin_bp.route("/brands/new", methods=["GET", "POST"])
def brands_new():
    form = BrandForm()
    if form.validate_on_submit():
        if Brand.query.filter_by(slug=form.slug.data).first():
            flash("이미 존재하는 슬러그입니다.", "error")
        else:
            b = Brand(
                name=form.name.data,
                slug=form.slug.data,
                sort_order=form.sort_order.data or 0,
                is_visible=form.is_visible.data,
            )
            db.session.add(b)
            db.session.commit()
            flash("브랜드가 등록되었습니다. 이어서 로고를 업로드하세요.", "success")
            return redirect(url_for("admin.brands_edit", brand_id=b.id))
    return render_template("admin/brand_form.html", form=form, brand=None)


@admin_bp.route("/brands/<int:brand_id>/edit", methods=["GET", "POST"])
def brands_edit(brand_id: int):
    b = Brand.query.get_or_404(brand_id)
    form = BrandForm(obj=b)
    if form.validate_on_submit():
        # If slug is being changed, check uniqueness
        if form.slug.data != b.slug and Brand.query.filter_by(slug=form.slug.data).first():
            flash("이미 존재하는 슬러그입니다.", "error")
        else:
            b.name = form.name.data
            b.slug = form.slug.data
            b.sort_order = form.sort_order.data or 0
            b.is_visible = form.is_visible.data
            db.session.commit()
            flash("저장되었습니다.", "success")
            return redirect(url_for("admin.brands_edit", brand_id=b.id))
    return render_template("admin/brand_form.html", form=form, brand=b)


@admin_bp.route("/brands/<int:brand_id>/delete", methods=["POST"])
def brands_delete(brand_id: int):
    from sqlalchemy.exc import IntegrityError
    b = Brand.query.get_or_404(brand_id)
    try:
        db.session.delete(b)
        db.session.commit()
        flash("브랜드가 삭제되었습니다.", "success")
    except IntegrityError:
        db.session.rollback()
        flash("이 브랜드를 사용하는 차량이 있어 삭제할 수 없습니다.", "error")
    return redirect(url_for("admin.brands"))


# --- Banners --------------------------------------------------------------
@admin_bp.route("/banners")
def banners():
    items = Banner.query.order_by(Banner.sort_order.asc(), Banner.id.asc()).all()
    return render_template("admin/banners.html", banners=items)


@admin_bp.route("/banners/new", methods=["GET", "POST"])
def banners_new():
    form = BannerForm()
    if form.validate_on_submit():
        b = Banner(
            eyebrow=(form.eyebrow.data or None),
            title=(form.title.data or "배너"),
            subtitle=(form.subtitle.data or None),
            link_url=(form.link_url.data or None),
            sort_order=form.sort_order.data or 0,
            is_visible=form.is_visible.data,
        )
        db.session.add(b)
        db.session.commit()
        flash("배너가 등록되었습니다.", "success")
        return redirect(url_for("admin.banners"))
    return render_template("admin/banner_form.html", form=form, banner=None)


@admin_bp.route("/banners/<int:banner_id>/edit", methods=["GET", "POST"])
def banners_edit(banner_id: int):
    b = Banner.query.get_or_404(banner_id)
    form = BannerForm(obj=b)
    if form.validate_on_submit():
        b.eyebrow = form.eyebrow.data or None
        b.title = form.title.data
        b.subtitle = form.subtitle.data or None
        b.link_url = form.link_url.data or None
        # image_path는 폼에서 관리하지 않음 — /admin/api/banners/<id>/image 로만 갱신
        b.sort_order = form.sort_order.data or 0
        b.is_visible = form.is_visible.data
        db.session.commit()
        flash("저장되었습니다.", "success")
        return redirect(url_for("admin.banners"))
    return render_template("admin/banner_form.html", form=form, banner=b)


@admin_bp.route("/banners/<int:banner_id>/delete", methods=["POST"])
def banners_delete(banner_id: int):
    b = Banner.query.get_or_404(banner_id)
    db.session.delete(b)
    db.session.commit()
    flash("배너가 삭제되었습니다.", "success")
    return redirect(url_for("admin.banners"))


# --- Users (read-only) -----------------------------------------------------
@admin_bp.route("/users")
def users():
    items = User.query.filter_by(deleted_at=None).order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=items)


# --- Q&A (1:1 문의) ---------------------------------------------------------
@admin_bp.route("/qna")
def qna_list():
    items = (
        QnaPost.query.order_by(
            QnaPost.answered_at.isnot(None).asc(), QnaPost.created_at.desc()
        ).all()
    )
    return render_template("admin/qna_list.html", posts=items)


@admin_bp.route("/qna/<int:post_id>", methods=["GET", "POST"])
def qna_detail(post_id: int):
    post = QnaPost.query.get_or_404(post_id)
    form = QnaAnswerForm(obj=post)
    if form.validate_on_submit():
        post.answer = form.answer.data
        post.answered_at = datetime.utcnow()
        db.session.commit()
        flash("답변이 등록되었습니다.", "success")
        return redirect(url_for("admin.qna_list"))
    return render_template("admin/qna_detail.html", post=post, form=form)


@admin_bp.route("/qna/<int:post_id>/delete", methods=["POST"])
def qna_delete(post_id: int):
    post = QnaPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash("문의가 삭제되었습니다.", "success")
    return redirect(url_for("admin.qna_list"))


# --- Site settings ---------------------------------------------------------
@admin_bp.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        phone = (request.form.get("contact_phone") or "").strip()
        hours = (request.form.get("contact_hours") or "").strip()
        set_site_setting("contact_phone", phone)
        set_site_setting("contact_hours", hours)
        flash("저장되었습니다.", "success")
        return redirect(url_for("admin.settings"))
    return render_template(
        "admin/settings.html",
        contact_phone=get_contact_phone(),
        contact_hours=get_contact_hours(),
    )
