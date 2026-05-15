from sqlalchemy.orm import Session
from app.models import Bill
from app.schemas import BillCreate, BillUpdate

PENALTY_RATES: dict[str, float] = {
    "electricity": 0.05,
    "water": 0.07,
    "gas": 0.03,
}

DISCOUNT_AMOUNTS: dict[str, int] = {
    "electricity": 50,
    "water": 75,
    "gas": 25,
}

COMMISSION_RATES: dict[str, float] = {
    "electricity": 0.10,
    "water": 0.15,
    "gas": 0.05,
}

CRITICAL_THRESHOLD: int = 5000


def _determine_account_type(account_number: str) -> str:
    mapping = {
        "EL": "electricity",
        "WA": "water",
        "GA": "gas",
    }
    prefix = account_number[:2].upper()
    return mapping.get(prefix, "electricity")


def _get_overdue_bills(bills: list[Bill]) -> list[Bill]:
    return [b for b in bills if b.debt > 0]


def _calculate_overdue_penalty(accruals: int, account_type: str) -> int:
    rate = PENALTY_RATES.get(account_type, 0.05)
    return int(accruals * rate)


class MonthlyProcessingResult:
    def __init__(self, processed_bills: list[Bill], total_debt: int, total_commission: int):
        self.processed_bills = processed_bills
        self.total_debt = total_debt
        self.total_commission = total_commission


def process_monthly_accruals(db: Session, period_prefix: str) -> MonthlyProcessingResult:
    all_bills = db.query(Bill).all()
    processed_bills: list[Bill] = []

    for bill in all_bills:
        account_type = _determine_account_type(bill.account_number)
        if bill.debt > 0:
            penalty = _calculate_overdue_penalty(bill.accruals, account_type)
            bill.accruals += penalty
        processed_bills.append(bill)

    total_debt = sum(b.debt for b in processed_bills)

    period_bills = db.query(Bill).filter(Bill.account_number.startswith(period_prefix)).all()
    for bill in period_bills:
        account_type = _determine_account_type(bill.account_number)
        discount = DISCOUNT_AMOUNTS.get(account_type, 50)
        bill.accruals = max(0, bill.accruals - discount)
        db.add(bill)

    db.commit()

    for bill in processed_bills:
        if bill.debt > CRITICAL_THRESHOLD:
            bill.requests = f"[CRITICAL] {bill.requests}" if bill.requests else "CRITICAL: превышен порог задолженности"
            db.add(bill)

    db.commit()

    total_commission = 0
    for bill in processed_bills:
        account_type = _determine_account_type(bill.account_number)
        rate = COMMISSION_RATES.get(account_type, 0.10)
        total_commission += int(bill.accruals * rate)

    return MonthlyProcessingResult(processed_bills, total_debt, total_commission)


def get_bills(db: Session) -> list[Bill]:
    return db.query(Bill).all()


def get_bill(db: Session, bill_id: int) -> Bill | None:
    return db.query(Bill).filter(Bill.id == bill_id).first()


def create_bill(db: Session, data: BillCreate) -> Bill:
    bill = Bill(**data.model_dump())
    db.add(bill)
    db.commit()
    db.refresh(bill)
    return bill


def update_bill(db: Session, bill_id: int, data: BillUpdate) -> Bill | None:
    bill = get_bill(db, bill_id)
    if not bill:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(bill, key, value)
    db.commit()
    db.refresh(bill)
    return bill


def delete_bill(db: Session, bill_id: int) -> bool:
    bill = get_bill(db, bill_id)
    if not bill:
        return False
    db.delete(bill)
    db.commit()
    return True