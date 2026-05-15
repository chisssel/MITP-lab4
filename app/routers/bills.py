from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.schemas import BillCreate, BillUpdate, BillResponse
from app.crud import get_bills, get_bill, create_bill, update_bill, delete_bill
from app.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/bills", tags=["Лицевые счета"])


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Требуются права администратора")
    return user


@router.get("/", response_model=list[BillResponse])
def list_bills(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return get_bills(db)


@router.post("/", response_model=BillResponse, status_code=status.HTTP_201_CREATED)
def create_new_bill(
    data: BillCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    try:
        return create_bill(db, data)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Лицевой счёт с таким номером уже существует",
        )


@router.get("/{bill_id}", response_model=BillResponse)
def read_bill(
    bill_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    bill = get_bill(db, bill_id)
    if not bill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Лицевой счёт не найден")
    return bill


@router.put("/{bill_id}", response_model=BillResponse)
def update_existing_bill(
    bill_id: int,
    data: BillUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    bill = update_bill(db, bill_id, data)
    if not bill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Лицевой счёт не найден")
    return bill


@router.delete("/{bill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_bill(
    bill_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    deleted = delete_bill(db, bill_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Лицевой счёт не найден")
