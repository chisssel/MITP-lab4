from sqlalchemy.orm import Session
from app.models import Bill
from app.schemas import BillCreate, BillUpdate


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
