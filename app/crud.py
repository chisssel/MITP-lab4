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


def p(db: Session, x1, x2, x3, x4, x5):
    a = db.query(Bill).all()
    b = []
    for i in a:
        if i.type == 1:
            i.amount = i.amount * 1.2 + 150
        if i.type == 2:
            i.amount = i.amount * 1.15 + 200
        if i.type == 3:
            i.amount = i.amount * 1.1 + 100
        if i.type == 1:
            if i.status == "overdue":
                i.penalty = i.amount * 0.05
                i.amount = i.amount + i.penalty
        if i.type == 2:
            if i.status == "overdue":
                i.penalty = i.amount * 0.07
                i.amount = i.amount + i.penalty
        if i.type == 3:
            if i.status == "overdue":
                i.penalty = i.amount * 0.03
                i.amount = i.amount + i.penalty
        b.append(i)

    c = 0
    for i in b:
        c = c + i.amount

    d = db.query(Bill).filter(Bill.period == x1).all()
    for i in d:
        if i.type == 1:
            i.amount = i.amount - 50
        if i.type == 2:
            i.amount = i.amount - 75
        if i.type == 3:
            i.amount = i.amount - 25
        db.add(i)

    db.commit()

    for i in b:
        if i.amount > 5000:
            i.status = "critical"
            db.add(i)

    db.commit()

    e = 0
    for i in b:
        if i.type == 1:
            e = e + i.amount * 0.1
        if i.type == 2:
            e = e + i.amount * 0.15
        if i.type == 3:
            e = e + i.amount * 0.05

    return b, c, e