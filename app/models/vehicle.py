from datetime import datetime
from app.extensions import db


PRODUCT_TYPES = ("subscription", "rent", "super")
VISIBILITY_STATES = ("public", "hidden", "soldout")
PLACEMENT_STATES = ("collection", "none")  # UpcomingSlot is the SSoT for upcoming
FUEL_TYPES = ("gasoline", "diesel", "hybrid", "ev", "lpg")
TRANSMISSION_TYPES = ("auto", "manual")


class Brand(db.Model):
    __tablename__ = "brand"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), unique=True, nullable=False)
    slug = db.Column(db.String(40), unique=True, nullable=False)
    logo_path = db.Column(db.String(255))
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    is_visible = db.Column(db.Boolean, default=True, nullable=False)

    vehicles = db.relationship("Vehicle", backref="brand", lazy="dynamic")


class Vehicle(db.Model):
    __tablename__ = "vehicle"

    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(
        db.Integer, db.ForeignKey("brand.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    model = db.Column(db.String(80), nullable=False)
    trim = db.Column(db.String(80))
    year = db.Column(db.Integer)
    color = db.Column(db.String(40))

    fuel = db.Column(db.Enum(*FUEL_TYPES, name="vehicle_fuel"))
    transmission = db.Column(db.Enum(*TRANSMISSION_TYPES, name="vehicle_transmission"))
    mileage_km = db.Column(db.Integer)
    plate = db.Column(db.String(20))  # internal-only, never expose to public
    new_price_man = db.Column(db.Integer)  # 신차가 (만원)

    headline = db.Column(db.String(200))
    description = db.Column(db.Text)
    options_json = db.Column(db.JSON)

    product_type = db.Column(
        db.Enum(*PRODUCT_TYPES, name="vehicle_product_type"),
        default="subscription",
        nullable=False,
    )
    price_min_man = db.Column(db.Integer)
    price_max_man = db.Column(db.Integer)

    visibility = db.Column(
        db.Enum(*VISIBILITY_STATES, name="vehicle_visibility"),
        default="hidden",
        nullable=False,
        index=True,
    )
    placement = db.Column(
        db.Enum(*PLACEMENT_STATES, name="vehicle_placement"),
        default="none",
        nullable=False,
        index=True,
    )
    is_featured = db.Column(db.Boolean, default=False, nullable=False)  # 에디터스 픽
    is_fast = db.Column(db.Boolean, default=False, nullable=False)      # 빠른 출고 배지
    is_deal = db.Column(db.Boolean, default=False, nullable=False)      # 특가 배지
    eta_label = db.Column(db.String(60))                                # 업커밍 라벨

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    images = db.relationship(
        "VehicleImage",
        backref="vehicle",
        order_by="VehicleImage.sort_order",
        cascade="all, delete-orphan",
        lazy="joined",
    )
    upcoming_slot = db.relationship(
        "UpcomingSlot",
        backref="vehicle",
        uselist=False,
        cascade="all, delete-orphan",
    )

    @property
    def brand_name(self) -> str:
        return self.brand.name if self.brand else ""

    @property
    def primary_image(self):
        for img in self.images:
            if img.is_primary:
                return img
        return self.images[0] if self.images else None

    @property
    def is_sold(self) -> bool:
        return self.visibility == "soldout"


class VehicleImage(db.Model):
    __tablename__ = "vehicle_image"

    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(
        db.Integer,
        db.ForeignKey("vehicle.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_path = db.Column(db.String(255), nullable=False)  # always posix-style
    is_primary = db.Column(db.Boolean, default=False, nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
