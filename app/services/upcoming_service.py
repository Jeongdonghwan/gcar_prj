"""Upcoming slot ordering service.

Single source of truth for upcoming page layout. PATCH payloads are validated
and applied within one transaction. UNIQUE(vehicle_id) is preserved by
deleting all rows in the affected groups first, then re-inserting in order.
"""
from typing import Iterable
from sqlalchemy import select
from sqlalchemy.sql import exists
from app.extensions import db
from app.models import UpcomingSlot, Vehicle


MAX_SLOTS_PER_GROUP = 50


class UpcomingPayloadError(ValueError):
    pass


def _validate_ids(ids: Iterable, label: str) -> list[int]:
    if not isinstance(ids, list):
        raise UpcomingPayloadError(f"{label} must be a list")
    out: list[int] = []
    seen: set[int] = set()
    for x in ids:
        if not isinstance(x, int) or isinstance(x, bool):
            raise UpcomingPayloadError(f"{label} contains non-integer id")
        if x in seen:
            raise UpcomingPayloadError(f"{label} contains duplicate id {x}")
        seen.add(x)
        out.append(x)
    if len(out) > MAX_SLOTS_PER_GROUP:
        raise UpcomingPayloadError(f"{label} exceeds max {MAX_SLOTS_PER_GROUP}")
    return out


def get_order() -> dict:
    rows = (
        db.session.query(UpcomingSlot)
        .order_by(UpcomingSlot.group.asc(), UpcomingSlot.position.asc())
        .all()
    )
    return {
        "group_a": [r.vehicle_id for r in rows if r.group == "a"],
        "group_b": [r.vehicle_id for r in rows if r.group == "b"],
    }


def reorder(group_a_ids: list[int], group_b_ids: list[int]) -> None:
    group_a = _validate_ids(group_a_ids, "group_a")
    group_b = _validate_ids(group_b_ids, "group_b")

    overlap = set(group_a) & set(group_b)
    if overlap:
        raise UpcomingPayloadError(f"vehicle ids appear in both groups: {sorted(overlap)}")

    all_ids = group_a + group_b
    if all_ids:
        existing = db.session.execute(
            select(Vehicle.id).where(Vehicle.id.in_(all_ids))
        ).scalars().all()
        missing = set(all_ids) - set(existing)
        if missing:
            raise UpcomingPayloadError(f"unknown vehicle ids: {sorted(missing)}")

    # Apply atomically
    UpcomingSlot.query.delete(synchronize_session=False)
    db.session.flush()

    for pos, vid in enumerate(group_a):
        db.session.add(UpcomingSlot(vehicle_id=vid, group="a", position=pos))
    for pos, vid in enumerate(group_b):
        db.session.add(UpcomingSlot(vehicle_id=vid, group="b", position=pos))
    db.session.commit()


def add_to_group(vehicle_id: int, group: str) -> None:
    if group not in ("a", "b"):
        raise UpcomingPayloadError("group must be 'a' or 'b'")
    if not db.session.get(Vehicle, vehicle_id):
        raise UpcomingPayloadError(f"vehicle {vehicle_id} not found")
    existing = UpcomingSlot.query.filter_by(vehicle_id=vehicle_id).first()
    if existing:
        existing.group = group
        existing.position = _next_position(group)
    else:
        db.session.add(
            UpcomingSlot(
                vehicle_id=vehicle_id, group=group, position=_next_position(group)
            )
        )
    db.session.commit()


def remove(vehicle_id: int) -> None:
    UpcomingSlot.query.filter_by(vehicle_id=vehicle_id).delete()
    db.session.commit()


def _next_position(group: str) -> int:
    last = (
        UpcomingSlot.query.filter_by(group=group)
        .order_by(UpcomingSlot.position.desc())
        .first()
    )
    return (last.position + 1) if last else 0


def unassigned_vehicles(limit: int = 50) -> list[Vehicle]:
    """Vehicles eligible to appear in upcoming but not yet placed."""
    placed = select(UpcomingSlot.vehicle_id)
    q = (
        Vehicle.query.filter(Vehicle.id.notin_(placed))
        .filter(Vehicle.visibility != "hidden")
        .order_by(Vehicle.created_at.desc())
        .limit(limit)
    )
    return q.all()
