import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite:///./test_housing.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def sample_bill():
    return {
        "account_number": "001-00001",
        "address": "ул. Ленина, д.1, кв.1",
        "owner_name": "Иванов И.И.",
        "service_type": "electricity",
    }


class TestCreateBill:
    def test_create_bill_success(self):
        resp = client.post("/bills/", json=sample_bill())
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["account_number"] == "001-00001"
        assert data["owner_name"] == "Иванов И.И."
        assert data["debt"] == 500

    def test_create_bill_duplicate_account(self):
        client.post("/bills/", json=sample_bill())
        resp = client.post("/bills/", json=sample_bill())
        assert resp.status_code == status.HTTP_409_CONFLICT

    def test_create_bill_empty_account_number(self):
        body = sample_bill()
        body["account_number"] = ""
        resp = client.post("/bills/", json=body)
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_create_bill_negative_readings(self):
        body = sample_bill()
        body["readings"] = -1
        resp = client.post("/bills/", json=body)
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_create_bill_negative_accruals(self):
        body = sample_bill()
        body["accruals"] = -100
        resp = client.post("/bills/", json=body)
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestListBills:
    def test_list_empty(self):
        resp = client.get("/bills/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json() == []

    def test_list_multiple(self):
        client.post("/bills/", json=sample_bill())
        b2 = sample_bill()
        b2["account_number"] = "001-00002"
        client.post("/bills/", json=b2)
        resp = client.get("/bills/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert len(data) == 2


class TestReadBill:
    def test_read_bill_success(self):
        create_resp = client.post("/bills/", json=sample_bill())
        bill_id = create_resp.json()["id"]
        resp = client.get(f"/bills/{bill_id}")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["id"] == bill_id

    def test_read_bill_not_found(self):
        resp = client.get("/bills/9999")
        assert resp.status_code == status.HTTP_404_NOT_FOUND
        assert "не найден" in resp.json()["detail"]

    def test_read_bill_invalid_id(self):
        resp = client.get("/bills/abc")
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestUpdateBill:
    def test_update_bill_full(self):
        create_resp = client.post("/bills/", json=sample_bill())
        bill_id = create_resp.json()["id"]
        updates = {
            "account_number": "001-99999",
            "address": "ул. Новая, д.5",
            "owner_name": "Петров П.П.",
            "readings": 2000,
            "accruals": 5000,
            "payments": 5000,
            "requests": "Всё исправлено",
        }
        resp = client.put(f"/bills/{bill_id}", json=updates)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["account_number"] == "001-99999"
        assert data["owner_name"] == "Петров П.П."
        assert data["debt"] == 0

    def test_update_bill_partial(self):
        create_resp = client.post("/bills/", json=sample_bill())
        bill_id = create_resp.json()["id"]
        resp = client.put(f"/bills/{bill_id}", json={"readings": 9999})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["readings"] == 9999

    def test_update_bill_not_found(self):
        resp = client.put("/bills/9999", json={"readings": 100})
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_update_bill_invalid_data(self):
        create_resp = client.post("/bills/", json=sample_bill())
        bill_id = create_resp.json()["id"]
        resp = client.put(f"/bills/{bill_id}", json={"readings": -5})
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestDeleteBill:
    def test_delete_bill_success(self):
        create_resp = client.post("/bills/", json=sample_bill())
        bill_id = create_resp.json()["id"]
        resp = client.delete(f"/bills/{bill_id}")
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        get_resp = client.get(f"/bills/{bill_id}")
        assert get_resp.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_bill_not_found(self):
        resp = client.delete("/bills/9999")
        assert resp.status_code == status.HTTP_404_NOT_FOUND


class TestWrongMethods:
    def test_patch_not_allowed(self):
        resp = client.patch("/bills/1", json={})
        assert resp.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_post_to_bill_detail_not_allowed(self):
        resp = client.post("/bills/1", json={})
        assert resp.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


class TestIntegration:
    def test_full_lifecycle(self):
        resp = client.post("/bills/", json=sample_bill())
        assert resp.status_code == status.HTTP_201_CREATED
        bill_id = resp.json()["id"]

        resp = client.get(f"/bills/{bill_id}")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["readings"] == 1500

        resp = client.put(f"/bills/{bill_id}", json={"readings": 2000, "payments": 3500})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["debt"] == 0

        resp = client.delete(f"/bills/{bill_id}")
        assert resp.status_code == status.HTTP_204_NO_CONTENT

        resp = client.get(f"/bills/{bill_id}")
        assert resp.status_code == status.HTTP_404_NOT_FOUND
