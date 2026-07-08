from urllib.parse import urlparse, urljoin
from flask import flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db
from app.forms.auth_forms import LoginForm, SignupForm
from app.models import User
from . import auth_bp


def _safe_next(target: str | None) -> str | None:
    if not target:
        return None
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    if test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc:
        return target
    return None


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user is None or not user.check_password(form.password.data) or not user.is_active:
            flash("이메일 또는 비밀번호가 올바르지 않습니다.", "error")
        else:
            login_user(user, remember=form.remember.data)
            next_url = _safe_next(request.args.get("next")) or url_for("public.index")
            return redirect(next_url)
    return render_template("auth/login.html", form=form, tab="login")


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))
    form = SignupForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        if User.query.filter_by(email=email).first():
            flash("이미 가입된 이메일입니다.", "error")
        else:
            user = User(
                email=email,
                name=form.name.data.strip(),
                phone=form.phone.data.strip(),
                marketing_opt_in=form.agree_marketing.data,
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("가입을 환영합니다.", "success")
            return redirect(url_for("public.index"))
    return render_template("auth/login.html", form=form, tab="signup")


@auth_bp.route("/logout", methods=["POST", "GET"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("public.index"))


# --- Kakao OAuth ------------------------------------------------------------
@auth_bp.route("/kakao")
def kakao_start():
    from app.services.kakao_oauth import build_authorize_url, new_state
    state = new_state()
    session["kakao_state"] = state
    next_target = _safe_next(request.args.get("next"))
    if next_target:
        session["kakao_next"] = next_target
    return redirect(build_authorize_url(state))


@auth_bp.route("/kakao/callback")
def kakao_callback():
    from app.services.kakao_oauth import exchange_code, fetch_profile

    state_sent = session.pop("kakao_state", None)
    state_received = request.args.get("state")
    if not state_sent or state_sent != state_received:
        flash("로그인 요청을 검증할 수 없습니다. 다시 시도해주세요.", "error")
        return redirect(url_for("auth.login"))

    code = request.args.get("code")
    if not code:
        flash("카카오 인증이 취소되었습니다.", "error")
        return redirect(url_for("auth.login"))

    try:
        token = exchange_code(code)
        profile = fetch_profile(token["access_token"])
    except Exception:
        flash("카카오 로그인에 실패했습니다.", "error")
        return redirect(url_for("auth.login"))

    kakao_id = str(profile.get("id"))
    kakao_account = profile.get("kakao_account", {}) or {}
    email = (kakao_account.get("email") or "").lower() or None
    nickname = (kakao_account.get("profile") or {}).get("nickname")
    phone = kakao_account.get("phone_number")

    user = User.query.filter_by(kakao_id=kakao_id).first()
    if user is None:
        if email:
            existing = User.query.filter_by(email=email).first()
            if existing is not None and existing.kakao_id is None:
                # 동일 이메일 일반회원 — 연결 확인 페이지로
                session["kakao_link_candidate_id"] = existing.id
                session["kakao_link_payload"] = {"kakao_id": kakao_id, "email": email}
                return redirect(url_for("auth.kakao_link_confirm"))
        user = User(
            kakao_id=kakao_id,
            email=email,
            name=nickname or "",
            phone=phone or "",
        )
        db.session.add(user)
        db.session.commit()

    login_user(user)
    next_url = _safe_next(session.pop("kakao_next", None)) or url_for("public.index")
    return redirect(next_url)


@auth_bp.route("/kakao/link", methods=["GET", "POST"])
def kakao_link_confirm():
    candidate_id = session.get("kakao_link_candidate_id")
    payload = session.get("kakao_link_payload") or {}
    if not candidate_id or not payload:
        return redirect(url_for("auth.login"))
    user = db.session.get(User, candidate_id)
    if not user:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        if request.form.get("action") == "link":
            user.kakao_id = payload["kakao_id"]
            db.session.commit()
            session.pop("kakao_link_candidate_id", None)
            session.pop("kakao_link_payload", None)
            login_user(user)
            flash("카카오 계정이 기존 회원과 연결되었습니다.", "success")
            return redirect(url_for("public.index"))
        session.pop("kakao_link_candidate_id", None)
        session.pop("kakao_link_payload", None)
        return redirect(url_for("auth.login"))

    return render_template("auth/kakao_link.html", user=user, payload=payload)
