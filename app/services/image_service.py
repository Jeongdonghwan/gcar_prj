"""Image upload and management.

Uploads land in `_tmp/{session_uuid}/` during new-vehicle drafts and are moved
into `vehicles/{vehicle_id}/` on save. EXIF orientation is normalized via
Pillow's `exif_transpose`. Filenames are randomized to avoid collisions and
disclosure of original names.
"""
import os
import shutil
import uuid
from io import BytesIO
from pathlib import Path
from typing import Optional

from PIL import Image, ImageOps, UnidentifiedImageError
from flask import current_app
from werkzeug.datastructures import FileStorage

from app.extensions import db
from app.models import VehicleImage


MAX_IMAGE_DIM = 2400
THUMB_DIM = 800


class ImageError(Exception):
    pass


def _allowed_ext(filename: str) -> Optional[str]:
    if "." not in filename:
        return None
    ext = filename.rsplit(".", 1)[1].lower()
    if ext not in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        return None
    return "jpg" if ext == "jpeg" else ext


def _verify_image(raw: bytes) -> None:
    try:
        with Image.open(BytesIO(raw)) as im:
            im.verify()
    except (UnidentifiedImageError, Exception) as e:
        raise ImageError(f"invalid image: {e}")


def _save_normalized(raw: bytes, dest: Path) -> None:
    with Image.open(BytesIO(raw)) as im:
        im = ImageOps.exif_transpose(im)
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGB")
        if im.width > MAX_IMAGE_DIM or im.height > MAX_IMAGE_DIM:
            im.thumbnail((MAX_IMAGE_DIM, MAX_IMAGE_DIM))
        dest.parent.mkdir(parents=True, exist_ok=True)
        suffix = dest.suffix.lower()
        if suffix in (".jpg", ".jpeg"):
            im.convert("RGB").save(dest, format="JPEG", quality=88, optimize=True)
        elif suffix == ".png":
            im.save(dest, format="PNG", optimize=True)
        elif suffix == ".webp":
            im.save(dest, format="WEBP", quality=88, method=6)
        else:
            im.save(dest)


def save_uploaded_file(file_storage: FileStorage, target_dir: Path) -> Path:
    """Save a single uploaded file to target_dir with a random name. Returns the saved Path."""
    ext = _allowed_ext(file_storage.filename or "")
    if ext is None:
        raise ImageError("허용되지 않은 파일 형식입니다.")
    raw = file_storage.read()
    if not raw:
        raise ImageError("빈 파일입니다.")
    if len(raw) > current_app.config["MAX_CONTENT_LENGTH"]:
        raise ImageError("파일이 너무 큽니다.")
    _verify_image(raw)

    target_dir.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}.{ext}"
    dest = target_dir / name
    _save_normalized(raw, dest)
    return dest


def upload_for_vehicle(vehicle_id: int, file_storage: FileStorage) -> VehicleImage:
    """Persist an uploaded image directly to a saved vehicle's directory."""
    target_dir = Path(current_app.config["UPLOAD_VEHICLES_DIR"]) / str(vehicle_id)
    saved_path = save_uploaded_file(file_storage, target_dir)
    rel_path = _to_static_url(saved_path)

    last = (
        VehicleImage.query.filter_by(vehicle_id=vehicle_id)
        .order_by(VehicleImage.sort_order.desc())
        .first()
    )
    next_order = (last.sort_order + 1) if last else 0
    has_primary = VehicleImage.query.filter_by(vehicle_id=vehicle_id, is_primary=True).first()

    img = VehicleImage(
        vehicle_id=vehicle_id,
        file_path=rel_path,
        is_primary=(has_primary is None),
        sort_order=next_order,
    )
    db.session.add(img)
    db.session.commit()
    return img


def upload_for_banner(banner_id: int, file_storage: FileStorage) -> str:
    """Save an uploaded hero banner image. Returns /static/... URL."""
    from app.models import Banner
    root = Path(current_app.config["UPLOAD_ROOT"]) / "banners"
    target_dir = root / str(banner_id)
    saved_path = save_uploaded_file(file_storage, target_dir)
    rel_path = _to_static_url(saved_path)

    banner = db.session.get(Banner, banner_id)
    if banner:
        banner.image_path = rel_path
        db.session.commit()
    return rel_path


def upload_for_brand(brand_id: int, file_storage: FileStorage) -> str:
    """Save an uploaded brand logo. Returns the /static/... URL to store in Brand.logo_path."""
    from app.models import Brand
    target_dir = Path(current_app.config["UPLOAD_BRANDS_DIR"]) / str(brand_id)
    saved_path = save_uploaded_file(file_storage, target_dir)
    rel_path = _to_static_url(saved_path)

    brand = db.session.get(Brand, brand_id)
    if brand:
        brand.logo_path = rel_path
        db.session.commit()
    return rel_path


def delete_image(image_id: int) -> None:
    img = VehicleImage.query.get(image_id)
    if not img:
        return
    abs_path = _absolute_path_from_static_url(img.file_path)
    try:
        if abs_path.exists():
            abs_path.unlink()
    except OSError:
        pass
    vid = img.vehicle_id
    was_primary = img.is_primary
    db.session.delete(img)
    db.session.flush()

    if was_primary:
        remaining = (
            VehicleImage.query.filter_by(vehicle_id=vid)
            .order_by(VehicleImage.sort_order.asc())
            .first()
        )
        if remaining:
            remaining.is_primary = True
    db.session.commit()


def set_primary(image_id: int) -> None:
    img = VehicleImage.query.get(image_id)
    if not img:
        return
    VehicleImage.query.filter_by(vehicle_id=img.vehicle_id).update({"is_primary": False})
    img.is_primary = True
    db.session.commit()


def reorder_images(vehicle_id: int, image_ids: list[int]) -> None:
    rows = {i.id: i for i in VehicleImage.query.filter_by(vehicle_id=vehicle_id).all()}
    for pos, iid in enumerate(image_ids):
        row = rows.get(iid)
        if row:
            row.sort_order = pos
    db.session.commit()


def _to_static_url(abs_path: Path) -> str:
    """Convert absolute upload path to '/static/uploads/...' URL form."""
    root = Path(current_app.root_path)
    rel = abs_path.resolve().relative_to(root.resolve())
    # rel starts with 'static/uploads/...'
    return "/" + rel.as_posix()


def _absolute_path_from_static_url(static_url: str) -> Path:
    root = Path(current_app.root_path)
    rel = static_url.lstrip("/")
    return (root / rel).resolve()


def remove_vehicle_dir(vehicle_id: int) -> None:
    d = Path(current_app.config["UPLOAD_VEHICLES_DIR"]) / str(vehicle_id)
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)


def cleanup_tmp(max_age_hours: int = 24) -> int:
    """Delete _tmp subdirectories older than max_age_hours. Returns removed count."""
    tmp_root = Path(current_app.config["UPLOAD_TMP_DIR"])
    if not tmp_root.exists():
        return 0
    import time
    cutoff = time.time() - max_age_hours * 3600
    removed = 0
    for sub in tmp_root.iterdir():
        if sub.is_dir() and sub.stat().st_mtime < cutoff:
            shutil.rmtree(sub, ignore_errors=True)
            removed += 1
    return removed
