from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class ServiceType(enum.Enum):
    ELECTRICITY = "electricity"
    WATER = "water"
    GAS = "gas"
    HEATING = "heating"


class RequestStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="user")
    created_at = Column(DateTime, default=_utcnow)


class Bill(Base):
    __tablename__ = "bills"

    id = Column(Integer, primary_key=True, index=True)
    account_number = Column(String(50), unique=True, nullable=False, index=True)
    address = Column(String(200), nullable=False, index=True)
    owner_name = Column(String(100), nullable=False)
    service_type = Column(String(50), default=ServiceType.ELECTRICITY.value, nullable=False, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    readings = relationship("MeterReading", back_populates="bill", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="bill", cascade="all, delete-orphan")
    service_requests = relationship("ServiceRequest", back_populates="bill", cascade="all, delete-orphan")

    @property
    def total_accruals(self) -> int:
        return sum(p.reading_value for p in self.readings)

    @property
    def total_payments(self) -> int:
        return sum(p.amount for p in self.payments)

    @property
    def debt(self) -> int:
        return self.total_accruals - self.total_payments


class MeterReading(Base):
    __tablename__ = "meter_readings"

    id = Column(Integer, primary_key=True, index=True)
    bill_id = Column(Integer, ForeignKey("bills.id", ondelete="CASCADE"), nullable=False, index=True)
    reading_value = Column(Integer, nullable=False)
    reading_date = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=_utcnow)

    bill = relationship("Bill", back_populates="readings")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    bill_id = Column(Integer, ForeignKey("bills.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Integer, nullable=False)
    payment_date = Column(DateTime, nullable=False, index=True)
    payment_method = Column(String(50), default="cash")
    transaction_id = Column(String(100), unique=True, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    bill = relationship("Bill", back_populates="payments")


class ServiceRequest(Base):
    __tablename__ = "service_requests"

    id = Column(Integer, primary_key=True, index=True)
    bill_id = Column(Integer, ForeignKey("bills.id", ondelete="CASCADE"), nullable=False, index=True)
    request_type = Column(String(100), nullable=False)
    description = Column(String(500))
    status = Column(String(50), default=RequestStatus.PENDING.value, nullable=False, index=True)
    priority = Column(Integer, default=0)
    created_at = Column(DateTime, default=_utcnow, index=True)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    completed_at = Column(DateTime, nullable=True)

    bill = relationship("Bill", back_populates="service_requests")