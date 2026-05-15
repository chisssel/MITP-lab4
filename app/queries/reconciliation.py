from datetime import datetime
from typing import List, Tuple

from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.models import Bill, MeterReading, Payment


def get_debt_summary(
    db: Session,
    period_start: datetime,
    period_end: datetime,
) -> List[Tuple[str, str, str, int, int, int]]:
    debt_expr = func.coalesce(func.sum(MeterReading.reading_value), 0) - func.coalesce(
        func.sum(Payment.amount), 0
    )
    rows = (
        db.query(
            Bill.account_number,
            Bill.address,
            Bill.owner_name,
            func.coalesce(func.sum(MeterReading.reading_value), 0).label("total_readings"),
            func.coalesce(func.sum(Payment.amount), 0).label("total_payments"),
        )
        .outerjoin(
            MeterReading,
            (MeterReading.bill_id == Bill.id)
            & (MeterReading.reading_date >= period_start)
            & (MeterReading.reading_date < period_end),
        )
        .outerjoin(
            Payment,
            (Payment.bill_id == Bill.id)
            & (Payment.payment_date >= period_start)
            & (Payment.payment_date < period_end),
        )
        .group_by(Bill.id, Bill.account_number, Bill.address, Bill.owner_name)
        .having(debt_expr > 0)
        .order_by(desc(debt_expr))
        .all()
    )
    return [(r.account_number, r.address, r.owner_name, r.total_readings, r.total_payments,
             r.total_readings - r.total_payments) for r in rows]
