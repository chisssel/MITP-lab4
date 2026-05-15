from sqlalchemy import Column, Integer, String
from app.database import Base


class Bill(Base):
    __tablename__ = "bills"

    id = Column(Integer, primary_key=True, index=True)
    account_number = Column(String, unique=True, nullable=False, index=True)
    address = Column(String, nullable=False)
    owner_name = Column(String, nullable=False)
    readings = Column(Integer, default=0, nullable=False)
    accruals = Column(Integer, default=0, nullable=False)
    payments = Column(Integer, default=0, nullable=False)
    requests = Column(String, default="")

    @property
    def debt(self) -> int:
        return self.accruals - self.payments
