from fastapi import FastAPI
from app.database import engine, Base
from app.routers import bills

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Система управления ЖКХ",
    description="API для управления лицевыми счетами в системе ЖКХ",
    version="1.0.0",
)

app.include_router(bills.router)
