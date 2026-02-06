import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.auth import get_password_hash
from app.db_models import User

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def client():
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def auth_client(client):
    # Create test user
    db = TestingSessionLocal()
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("testpass"),
        first_name="Test",
        last_name="User",
        role="user"
    )
    db.add(user)
    db.commit()
    db.close()

    # Login to get token
    response = client.post("/api/auth/login", json={
        "username": "testuser",
        "password": "testpass"
    })
    token = response.json()["access_token"]
    client.headers = {"Authorization": f"Bearer {token}"}
    return client


class TestHealth:
    def test_health_check(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestAuth:
    def test_register_user(self, client):
        response = client.post("/api/auth/register", json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpass123",
            "first_name": "New",
            "last_name": "User"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"

    def test_login(self, client):
        # First register
        client.post("/api/auth/register", json={
            "username": "loginuser",
            "email": "login@example.com",
            "password": "loginpass"
        })

        # Then login
        response = client.post("/api/auth/login", json={
            "username": "loginuser",
            "password": "loginpass"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_invalid_credentials(self, client):
        response = client.post("/api/auth/login", json={
            "username": "nonexistent",
            "password": "wrongpass"
        })
        assert response.status_code == 401


class TestAccounts:
    def test_create_account(self, auth_client):
        response = auth_client.post("/api/accounts", json={
            "name": "Test Account",
            "phone": "555-1234"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Account"
        assert data["phone"] == "555-1234"

    def test_list_accounts(self, auth_client):
        # Create an account
        auth_client.post("/api/accounts", json={"name": "Account 1"})
        auth_client.post("/api/accounts", json={"name": "Account 2"})

        response = auth_client.get("/api/accounts")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    def test_get_account(self, auth_client):
        # Create an account
        create_response = auth_client.post("/api/accounts", json={"name": "Get Test"})
        account_id = create_response.json()["id"]

        response = auth_client.get(f"/api/accounts/{account_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Get Test"

    def test_update_account(self, auth_client):
        # Create an account
        create_response = auth_client.post("/api/accounts", json={"name": "Original"})
        account_id = create_response.json()["id"]

        response = auth_client.put(f"/api/accounts/{account_id}", json={"name": "Updated"})
        assert response.status_code == 200
        assert response.json()["name"] == "Updated"

    def test_delete_account(self, auth_client):
        # Create an account
        create_response = auth_client.post("/api/accounts", json={"name": "To Delete"})
        account_id = create_response.json()["id"]

        response = auth_client.delete(f"/api/accounts/{account_id}")
        assert response.status_code == 204


class TestContacts:
    def test_create_contact(self, auth_client):
        response = auth_client.post("/api/contacts", json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"

    def test_list_contacts(self, auth_client):
        auth_client.post("/api/contacts", json={"last_name": "Contact1"})
        auth_client.post("/api/contacts", json={"last_name": "Contact2"})

        response = auth_client.get("/api/contacts")
        assert response.status_code == 200
        assert response.json()["total"] == 2


class TestLeads:
    def test_create_lead(self, auth_client):
        response = auth_client.post("/api/leads", json={
            "first_name": "Lead",
            "last_name": "Test",
            "company": "Test Co",
            "email": "lead@test.com"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["last_name"] == "Test"
        assert data["company"] == "Test Co"

    def test_convert_lead(self, auth_client):
        # Create a lead
        create_response = auth_client.post("/api/leads", json={
            "first_name": "Convert",
            "last_name": "Me",
            "company": "Convert Co"
        })
        lead_id = create_response.json()["id"]

        # Convert the lead
        response = auth_client.post(f"/api/leads/{lead_id}/convert", json={
            "create_account": True,
            "create_opportunity": True
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["contact_id"] is not None


class TestCases:
    def test_create_case(self, auth_client):
        response = auth_client.post("/api/cases", json={
            "subject": "Test Case",
            "description": "This is a test",
            "priority": "High"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["subject"] == "Test Case"
        assert data["priority"] == "High"
        assert "case_number" in data

    def test_escalate_case(self, auth_client):
        # Create a case
        create_response = auth_client.post("/api/cases", json={
            "subject": "Escalate Test",
            "priority": "Critical"
        })
        case_id = create_response.json()["id"]

        # Escalate
        response = auth_client.post(f"/api/cases/{case_id}/escalate")
        assert response.status_code == 200
        assert response.json()["is_escalated"] == True


class TestOpportunities:
    def test_create_opportunity(self, auth_client):
        response = auth_client.post("/api/opportunities", json={
            "name": "Big Deal",
            "amount": 50000,
            "stage": "Prospecting"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Big Deal"
        assert data["amount"] == 50000


class TestDashboard:
    def test_get_stats(self, auth_client):
        response = auth_client.get("/api/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        assert "leads_count" in data
        assert "opportunities_count" in data

    def test_search(self, auth_client):
        # Create some data
        auth_client.post("/api/accounts", json={"name": "Searchable Account"})

        response = auth_client.get("/api/dashboard/search?q=Searchable")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) > 0
