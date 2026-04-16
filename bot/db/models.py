from datetime import datetime
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Enum, Float, ForeignKey,
    Integer, String, Text, func,
)
from sqlalchemy.orm import DeclarativeBase, relationship
import enum


class Base(DeclarativeBase):
    pass


# ── Enums ──────────────────────────────────────────────

class Language(str, enum.Enum):
    RU = "ru"
    UZ = "uz"


class ProfileType(str, enum.Enum):
    SON = "son"        # ищем невестку
    DAUGHTER = "daughter"  # анкета дочери


class ProfileStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"      # на проверке модератором
    PUBLISHED = "published"
    REJECTED = "rejected"
    PAUSED = "paused"
    DELETED = "deleted"


class VipStatus(str, enum.Enum):
    NONE = "none"
    ACTIVE = "active"
    EXPIRED = "expired"


class Education(str, enum.Enum):
    SECONDARY = "secondary"
    VOCATIONAL = "vocational"
    HIGHER = "higher"
    STUDYING = "studying"


class Housing(str, enum.Enum):
    OWN_HOUSE = "own_house"
    OWN_APARTMENT = "own_apartment"
    WITH_PARENTS = "with_parents"
    RENT = "rent"


class ParentHousing(str, enum.Enum):
    HOUSE = "house"
    APARTMENT = "apartment"


class CarStatus(str, enum.Enum):
    PERSONAL = "personal"
    FAMILY = "family"
    NONE = "none"


class ResidenceStatus(str, enum.Enum):
    UZBEKISTAN = "uzbekistan"
    CIS = "cis"
    USA = "usa"
    EUROPE = "europe"
    RESIDENCE_PERMIT = "residence_permit"
    CITIZENSHIP_OTHER = "citizenship_other"
    OTHER_COUNTRY = "other_country"


class Religiosity(str, enum.Enum):
    PRACTICING = "practicing"
    MODERATE = "moderate"
    SECULAR = "secular"


class MaritalStatus(str, enum.Enum):
    NEVER_MARRIED = "never_married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"


class ChildrenStatus(str, enum.Enum):
    NO = "no"
    YES_WITH_ME = "yes_with_me"
    YES_WITH_EX = "yes_with_ex"


class PhotoType(str, enum.Enum):
    REGULAR = "regular"
    CLOSED_FACE = "closed_face"
    SILHOUETTE = "silhouette"
    NONE = "none"


class FamilyPosition(str, enum.Enum):
    OLDEST = "oldest"
    MIDDLE = "middle"
    YOUNGEST = "youngest"
    ONLY = "only"


class SearchScope(str, enum.Enum):
    UZBEKISTAN_ONLY = "uzbekistan_only"
    DIASPORA = "diaspora"
    ANYWHERE = "anywhere"


class PaymentMethod(str, enum.Enum):
    PAYME = "payme"
    CLICK = "click"
    UZUM = "uzum"
    CARD_TRANSFER = "card_transfer"
    STRIPE = "stripe"
    MODERATOR = "moderator"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class ComplaintReason(str, enum.Enum):
    WRONG_DATA = "wrong_data"
    SUSPICIOUS = "suspicious"
    STOLEN_PHOTO = "stolen_photo"
    BAD_BEHAVIOR = "bad_behavior"
    OTHER = "other"


class ComplaintStatus(str, enum.Enum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    DISMISSED = "dismissed"


class RequestStatus(str, enum.Enum):
    PENDING = "pending"
    TALKING = "talking"
    CONTACT_GIVEN = "contact_given"
    REJECTED = "rejected"


class FeedbackResult(str, enum.Enum):
    NIKOH = "nikoh"
    TALKING = "talking"
    THINKING = "thinking"
    NOT_MATCHED = "not_matched"


# ── Models ─────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True)  # telegram user id
    language = Column(Enum(Language), default=Language.RU)
    consent_general = Column(Boolean, default=False)
    consent_special = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    profiles = relationship("Profile", back_populates="user")
    favorites = relationship("Favorite", back_populates="user", foreign_keys="Favorite.user_id")
    payments = relationship("Payment", back_populates="user")


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    profile_type = Column(Enum(ProfileType), nullable=False)
    status = Column(Enum(ProfileStatus), default=ProfileStatus.DRAFT)
    vip_status = Column(Enum(VipStatus), default=VipStatus.NONE)
    vip_expires_at = Column(DateTime, nullable=True)
    display_id = Column(String(20), unique=True, nullable=True)  # #ДД-2026-00023

    # Q1-Q4: basic info
    name = Column(String(100))
    birth_year = Column(Integer)
    height_cm = Column(Integer)
    weight_kg = Column(Integer)
    body_type = Column(String(20))  # slim / average / athletic / full

    # Q5: education
    education = Column(Enum(Education))
    university_info = Column(String(200))  # if studying

    # Q6: work
    occupation = Column(Text)

    # Q7: housing
    housing = Column(Enum(Housing))
    parent_housing_type = Column(Enum(ParentHousing), nullable=True)

    # Q8: car
    car = Column(Enum(CarStatus))

    # Q9: location
    city = Column(String(100))
    district = Column(String(100))
    address = Column(Text)  # confidential

    # Q10: residence status
    residence_status = Column(Enum(ResidenceStatus))

    # Q10B: travel mode / search scope
    search_scope = Column(Enum(SearchScope))
    preferred_city = Column(String(100))
    preferred_district = Column(String(100))
    preferred_country = Column(String(100))

    # Q11: family origin region
    family_region = Column(String(100))

    # Q12: nationality
    nationality = Column(String(50))

    # Q13-Q14: parents
    father_occupation = Column(Text)
    mother_occupation = Column(Text)

    # Q15: siblings
    brothers_count = Column(Integer, default=0)
    sisters_count = Column(Integer, default=0)
    family_position = Column(Enum(FamilyPosition))

    # Q16: religiosity
    religiosity = Column(Enum(Religiosity))

    # Q17: marital status
    marital_status = Column(Enum(MaritalStatus))

    # Q18: children
    children_status = Column(Enum(ChildrenStatus))

    # Q19: health
    health_notes = Column(Text)

    # Q20: character & hobbies
    character_hobbies = Column(Text)

    # Q20A: compatibility
    ideal_family_life = Column(Text)
    important_qualities = Column(Text)
    five_year_plans = Column(Text)

    # Q21: photo
    photo_type = Column(Enum(PhotoType), default=PhotoType.NONE)
    photo_file_id = Column(String(200))

    # Q22: contacts
    parent_phone = Column(String(20))
    parent_telegram = Column(String(100))
    candidate_telegram = Column(String(100))
    location_lat = Column(Float, nullable=True)
    location_lon = Column(Float, nullable=True)
    location_link = Column(Text, nullable=True)

    # Language the anketa was filled in
    anketa_lang = Column(String(5), default="ru")

    # Q23: active status
    is_active = Column(Boolean, default=True)

    # stats
    views_count = Column(Integer, default=0)
    requests_count = Column(Integer, default=0)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    published_at = Column(DateTime, nullable=True)
    last_reminder_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="profiles")
    requirements = relationship("Requirement", back_populates="profile", uselist=False)
    complaints_received = relationship("Complaint", back_populates="profile")


class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False, unique=True)

    age_from = Column(Integer)
    age_to = Column(Integer)
    education = Column(String(50))  # "higher", "vocational", "any"
    residence = Column(String(100))  # json or comma-separated
    residence_city = Column(String(100))
    residence_district = Column(String(100))
    nationality = Column(String(50))
    religiosity = Column(String(50))
    marital_status = Column(String(100))
    children = Column(String(50))  # "no_children", "any"
    # daughter-specific
    car_required = Column(String(50))
    housing_required = Column(String(50))
    job_required = Column(String(50))
    other_wishes = Column(Text)

    profile = relationship("Profile", back_populates="requirements")


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="favorites")
    profile = relationship("Profile")


class ContactRequest(Base):
    __tablename__ = "contact_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    requester_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    target_profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    status = Column(Enum(RequestStatus), default=RequestStatus.PENDING)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    requester = relationship("User")
    target_profile = relationship("Profile")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    amount = Column(Integer)  # in tiyin or cents
    currency = Column(String(10), default="UZS")
    method = Column(Enum(PaymentMethod))
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    transaction_id = Column(String(100))
    screenshot_file_id = Column(String(200))
    is_vip_payment = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    confirmed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="payments")
    profile = relationship("Profile")


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, autoincrement=True)
    reporter_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    reason = Column(Enum(ComplaintReason), nullable=False)
    details = Column(Text)
    status = Column(Enum(ComplaintStatus), default=ComplaintStatus.PENDING)
    created_at = Column(DateTime, server_default=func.now())

    reporter = relationship("User")
    profile = relationship("Profile", back_populates="complaints_received")


class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    meeting_date = Column(DateTime, nullable=False)
    notified_family = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User")
    profile = relationship("Profile")


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    result = Column(Enum(FeedbackResult), nullable=False)
    story = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User")
    profile = relationship("Profile")
