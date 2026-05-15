from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ServiceType(str, Enum):
    ELECTRICITY = "electricity"
    WATER = "water"
    GAS = "gas"
    HEATING = "heating"


class RequestStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"


class MeterReadingCreate(BaseModel):
    reading_value: int = Field(..., ge=0, description="Показание счётчика")
    reading_date: datetime


class MeterReadingResponse(BaseModel):
    id: int
    bill_id: int
    reading_value: int
    reading_date: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentCreate(BaseModel):
    amount: int = Field(..., gt=0, description="Сумма платежа")
    payment_date: datetime
    payment_method: Optional[str] = Field(default="cash", max_length=50)
    transaction_id: Optional[str] = Field(None, max_length=100)


class PaymentResponse(BaseModel):
    id: int
    bill_id: int
    amount: int
    payment_date: datetime
    payment_method: str
    transaction_id: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ServiceRequestCreate(BaseModel):
    request_type: str = Field(..., min_length=1, max_length=100, description="Тип заявки")
    description: Optional[str] = Field(None, max_length=500)
    priority: int = Field(default=0, ge=0, le=10)


class ServiceRequestUpdate(BaseModel):
    request_type: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    status: Optional[RequestStatus] = None
    priority: Optional[int] = Field(None, ge=0, le=10)


class ServiceRequestResponse(BaseModel):
    id: int
    bill_id: int
    request_type: str
    description: Optional[str]
    status: RequestStatus
    priority: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class BillCreate(BaseModel):
    account_number: str = Field(..., min_length=1, max_length=50, description="Номер лицевого счёта")
    address: str = Field(..., min_length=1, max_length=200, description="Адрес помещения")
    owner_name: str = Field(..., min_length=1, max_length=100, description="ФИО владельца")
    service_type: ServiceType = Field(default=ServiceType.ELECTRICITY, description="Тип услуги")


class BillUpdate(BaseModel):
    account_number: Optional[str] = Field(None, min_length=1, max_length=50)
    address: Optional[str] = Field(None, min_length=1, max_length=200)
    owner_name: Optional[str] = Field(None, min_length=1, max_length=100)
    service_type: Optional[ServiceType] = None


class BillResponse(BaseModel):
    id: int
    account_number: str
    address: str
    owner_name: str
    service_type: ServiceType
    total_accruals: int
    total_payments: int
    debt: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BillDetailResponse(BillResponse):
    readings: List[MeterReadingResponse] = []
    payments: List[PaymentResponse] = []
    service_requests: List[ServiceRequestResponse] = []