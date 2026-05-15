from pydantic import BaseModel, Field
from typing import Optional


class BillCreate(BaseModel):
    account_number: str = Field(..., min_length=1, max_length=50, description="Номер лицевого счёта")
    address: str = Field(..., min_length=1, max_length=200, description="Адрес помещения")
    owner_name: str = Field(..., min_length=1, max_length=100, description="ФИО владельца")
    readings: int = Field(default=0, ge=0, description="Показания счётчика")
    accruals: int = Field(default=0, ge=0, description="Начисления")
    payments: int = Field(default=0, ge=0, description="Оплаты")
    requests: Optional[str] = Field(default="", max_length=500, description="Заявки")


class BillUpdate(BaseModel):
    account_number: Optional[str] = Field(None, min_length=1, max_length=50)
    address: Optional[str] = Field(None, min_length=1, max_length=200)
    owner_name: Optional[str] = Field(None, min_length=1, max_length=100)
    readings: Optional[int] = Field(None, ge=0)
    accruals: Optional[int] = Field(None, ge=0)
    payments: Optional[int] = Field(None, ge=0)
    requests: Optional[str] = Field(None, max_length=500)


class BillResponse(BaseModel):
    id: int
    account_number: str
    address: str
    owner_name: str
    readings: int
    accruals: int
    payments: int
    requests: str
    debt: int

    model_config = {"from_attributes": True}
