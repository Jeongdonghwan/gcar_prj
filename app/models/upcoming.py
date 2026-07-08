from app.extensions import db


UPCOMING_GROUPS = ("a", "b")


class UpcomingSlot(db.Model):
    """SSoT for upcoming page ordering. One row per vehicle that appears in upcoming.

    Group A = '1달 내 출고 가능', Group B = '그 밖에 준비 중'.
    Position is per-group, ASC.
    """

    __tablename__ = "upcoming_slot"

    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(
        db.Integer,
        db.ForeignKey("vehicle.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    group = db.Column(db.Enum(*UPCOMING_GROUPS, name="upcoming_group"), nullable=False)
    position = db.Column(db.Integer, nullable=False)

    __table_args__ = (
        db.Index("ix_upcoming_group_position", "group", "position"),
    )
