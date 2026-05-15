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


@pytest.fixture
def admin_token():
    from app.models import User as UserModel
    client.post("/auth/register", json={"username": "admin", "password": "admin123"})
    db = TestingSessionLocal()
    user = db.query(UserModel).filter(UserModel.username == "admin").first()
    user.role = "admin"
    db.commit()
    db.close()
    resp = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    return resp.json()["access_token"]


@pytest.fixture
def user_token():
    client.post("/auth/register", json={"username": "user", "password": "user1234"})
    resp = client.post("/auth/login", json={"username": "user", "password": "user1234"})
    return resp.json()["access_token"]


@pytest.fixture
def admin_auth(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def user_auth(user_token):
    return {"Authorization": f"Bearer {user_token}"}


def sample_bill():
    return {
        "account_number": "001-00001",
        "address": "ул. Ленина, д.1, кв.1",
        "owner_name": "Иванов И.И.",
        "service_type": "electricity",
    }


class TestAuth:
    def test_register_and_login(self):
        resp = client.post("/auth/register", json={"username": "newuser", "password": "newpass1"})
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["username"] == "newuser"

        resp = client.post("/auth/login", json={"username": "newuser", "password": "newpass1"})
        assert resp.status_code == status.HTTP_200_OK
        assert "access_token" in resp.json()

    def test_login_wrong_password(self):
        client.post("/auth/register", json={"username": "u", "password": "password"})
        resp = client.post("/auth/login", json={"username": "u", "password": "wrong"})
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_register_duplicate(self):
        client.post("/auth/register", json={"username": "dup", "password": "pass1234"})
        resp = client.post("/auth/register", json={"username": "dup", "password": "pass1234"})
        assert resp.status_code == status.HTTP_409_CONFLICT


class TestCreateBill:
    def test_create_bill_success(self, admin_auth):
        resp = client.post("/bills/", json=sample_bill(), headers=admin_auth)
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["account_number"] == "001-00001"
        assert data["owner_name"] == "Иванов И.И."
        assert data["service_type"] == "electricity"

    def test_create_bill_unauthorized(self):
        resp = client.post("/bills/", json=sample_bill())
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_bill_forbidden_user(self, user_auth):
        resp = client.post("/bills/", json=sample_bill(), headers=user_auth)
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_create_bill_duplicate_account(self, admin_auth):
        client.post("/bills/", json=sample_bill(), headers=admin_auth)
        resp = client.post("/bills/", json=sample_bill(), headers=admin_auth)
        assert resp.status_code == status.HTTP_409_CONFLICT

    def test_create_bill_empty_account_number(self, admin_auth):
        body = sample_bill()
        body["account_number"] = ""
        resp = client.post("/bills/", json=body, headers=admin_auth)
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_bill_invalid_service_type(self, admin_auth):
        body = sample_bill()
        body["service_type"] = "invalid"
        resp = client.post("/bills/", json=body, headers=admin_auth)
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestListBills:
    def test_list_empty(self, admin_auth):
        resp = client.get("/bills/", headers=admin_auth)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json() == []

    def test_list_multiple(self, admin_auth):
        client.post("/bills/", json=sample_bill(), headers=admin_auth)
        b2 = sample_bill()
        b2["account_number"] = "001-00002"
        client.post("/bills/", json=b2, headers=admin_auth)
        resp = client.get("/bills/", headers=admin_auth)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert len(data) == 2

    def test_list_unauthorized(self):
        resp = client.get("/bills/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


class TestReadBill:
    def test_read_bill_success(self, admin_auth):
        create_resp = client.post("/bills/", json=sample_bill(), headers=admin_auth)
        bill_id = create_resp.json()["id"]
        resp = client.get(f"/bills/{bill_id}", headers=admin_auth)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["id"] == bill_id

    def test_read_bill_not_found(self, admin_auth):
        resp = client.get("/bills/9999", headers=admin_auth)
        assert resp.status_code == status.HTTP_404_NOT_FOUND
        assert "не найден" in resp.json()["detail"]

    def test_read_bill_invalid_id(self, admin_auth):
        resp = client.get("/bills/abc", headers=admin_auth)
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestUpdateBill:
    def test_update_bill_full(self, admin_auth):
        create_resp = client.post("/bills/", json=sample_bill(), headers=admin_auth)
        bill_id = create_resp.json()["id"]
        updates = {
            "account_number": "001-99999",
            "address": "ул. Новая, д.5",
            "owner_name": "Петров П.П.",
            "service_type": "water",
        }
        resp = client.put(f"/bills/{bill_id}", json=updates, headers=admin_auth)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["account_number"] == "001-99999"
        assert data["owner_name"] == "Петров П.П."

    def test_update_bill_partial(self, admin_auth):
        create_resp = client.post("/bills/", json=sample_bill(), headers=admin_auth)
        bill_id = create_resp.json()["id"]
        resp = client.put(f"/bills/{bill_id}", json={"owner_name": "Новое Имя"}, headers=admin_auth)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["owner_name"] == "Новое Имя"

    def test_update_bill_not_found(self, admin_auth):
        resp = client.put("/bills/9999", json={"owner_name": "x"}, headers=admin_auth)
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_update_bill_forbidden_user(self, user_auth, admin_auth):
        create_resp = client.post("/bills/", json=sample_bill(), headers=admin_auth)
        bill_id = create_resp.json()["id"]
        resp = client.put(f"/bills/{bill_id}", json={"owner_name": "x"}, headers=user_auth)
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_update_bill_mass_assignment_protected(self, admin_auth):
        create_resp = client.post("/bills/", json=sample_bill(), headers=admin_auth)
        bill_id = create_resp.json()["id"]
        resp = client.put(f"/bills/{bill_id}", json={"id": 999}, headers=admin_auth)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["id"] == bill_id


class TestDeleteBill:
    def test_delete_bill_success(self, admin_auth):
        create_resp = client.post("/bills/", json=sample_bill(), headers=admin_auth)
        bill_id = create_resp.json()["id"]
        resp = client.delete(f"/bills/{bill_id}", headers=admin_auth)
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        get_resp = client.get(f"/bills/{bill_id}", headers=admin_auth)
        assert get_resp.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_bill_not_found(self, admin_auth):
        resp = client.delete("/bills/9999", headers=admin_auth)
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_bill_forbidden_user(self, user_auth, admin_auth):
        create_resp = client.post("/bills/", json=sample_bill(), headers=admin_auth)
        bill_id = create_resp.json()["id"]
        resp = client.delete(f"/bills/{bill_id}", headers=user_auth)
        assert resp.status_code == status.HTTP_403_FORBIDDEN


class TestWrongMethods:
    def test_patch_not_allowed(self, admin_auth):
        resp = client.patch("/bills/1", json={}, headers=admin_auth)
        assert resp.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_post_to_bill_detail_not_allowed(self, admin_auth):
        resp = client.post("/bills/1", json={}, headers=admin_auth)
        assert resp.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


class TestIntegration:
    def test_full_lifecycle(self, admin_auth):
        resp = client.post("/bills/", json=sample_bill(), headers=admin_auth)
        assert resp.status_code == status.HTTP_201_CREATED
        bill_id = resp.json()["id"]

        resp = client.get(f"/bills/{bill_id}", headers=admin_auth)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["service_type"] == "electricity"

        resp = client.put(f"/bills/{bill_id}", json={"owner_name": "Новое Имя"}, headers=admin_auth)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["owner_name"] == "Новое Имя"

        resp = client.delete(f"/bills/{bill_id}", headers=admin_auth)
        assert resp.status_code == status.HTTP_204_NO_CONTENT

        resp = client.get(f"/bills/{bill_id}", headers=admin_auth)
        assert resp.status_code == status.HTTP_404_NOT_FOUND
