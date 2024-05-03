import pytest
import csv
import io
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from sbs.models import Base, Account
from sbs import schemas
from sbs.main import app, get_db, get_paginated_accounts, deposit

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base.metadata.create_all(bind=engine)


# def mock_get_db():
#     db_mock = MagicMock()
#     return db_mock
#
#
# app.dependency_overrides[get_db] = mock_get_db

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture()
def client():
    return TestClient(app)


def test_create_account(client):
    response = client.post(
        "/accounts",
        params={"name": "Test Account", "starting_balance": 100.0},
    )

    assert response.status_code == 200

    data = response.json()
    assert "account_id" in data
    assert "name" in data
    assert "balance" in data
    account_id = data['account_id']
    # Delete the account
    response_delete = client.delete(f"/accounts/{account_id}")
    assert response_delete.status_code == 200
    data = response_delete.json()
    assert data["message"] == f"Account with account_id '{account_id}' has been deleted."


def test_get_account(client):
    # Create an account
    response_create = client.post(
        "/accounts",
        params={"name": "Test Account", "starting_balance": 100.0},
    )
    assert response_create.status_code == 200
    account_id = response_create.json()["account_id"]

    # Retrieve the created account
    response_get = client.get(f"/accounts/{account_id}")
    assert response_get.status_code == 200

    data = response_get.json()
    assert data["account_id"] == account_id
    assert data["name"] == "Test Account"
    assert data["balance"] == 100.0

    # Delete the account

    response_delete = client.delete(f"/accounts/{account_id}")
    assert response_delete.status_code == 200
    data = response_delete.json()
    assert data["message"] == f"Account with account_id '{account_id}' has been deleted."




def test_update_account(client):
    # Create an account
    response_create = client.post(
        "/accounts",
        params={"name": "Test Account", "starting_balance": 100.0},
    )
    assert response_create.status_code == 200
    account_id = response_create.json()["account_id"]

    # Update the account
    response_update = client.put(
        f"/accounts/{account_id}",
        params={"name": "Updated Test Account", "balance": 200.0},
    )
    assert response_update.status_code == 200

    data = response_update.json()
    assert data["message"] == f"Account with account_id '{account_id}' has been updated."
    assert data["account"]["name"] == "Updated Test Account"
    assert data["account"]["balance"] == 200.0

    # Delete the account
    response_delete = client.delete(f"/accounts/{account_id}")
    assert response_delete.status_code == 200

    data = response_delete.json()
    assert data["message"] == f"Account with account_id '{account_id}' has been deleted."


def test_delete_account(client):
    # Create an account
    response_create = client.post(
        "/accounts",
        params={"name": "Test Account", "starting_balance": 100.0},
    )
    assert response_create.status_code == 200
    account_id = response_create.json()["account_id"]

    # Delete the account
    response_delete = client.delete(f"/accounts/{account_id}")
    assert response_delete.status_code == 200

    data = response_delete.json()
    assert data["message"] == f"Account with account_id '{account_id}' has been deleted."


def test_transfer(client):
    # Create sender and recipient accounts
    response_create_sender = client.post(
        "/accounts",
        params={"name": "Sender Account", "starting_balance": 500.0},
    )
    assert response_create_sender.status_code == 200
    sender_id = response_create_sender.json()["account_id"]
    print(response_create_sender.json())

    response_create_recipient = client.post(
        "/accounts",
        params={"name": "Recipient Account", "starting_balance": 0.0},
    )
    assert response_create_recipient.status_code == 200
    recipient_id = response_create_recipient.json()["account_id"]
    print(response_create_recipient.json())

    # Perform transfer
    response_transfer = client.put(
        f"/accounts/{sender_id}/transfer/{recipient_id}",
        params={"amount": 200.0},
    )
    assert response_transfer.status_code == 200

    data = response_transfer.json()
    assert data["message"] == "Transfer successful"
    assert data["sender"]["account_id"] == sender_id
    assert data["sender"]["balance"] == 300.0
    assert data["recipient"]["account_id"] == recipient_id

    # Delete the account
    response_delete = client.delete(f"/accounts/{sender_id}")
    assert response_delete.status_code == 200
    data = response_delete.json()
    assert data["message"] == f"Account with account_id '{sender_id}' has been deleted."

    response_delete = client.delete(f"/accounts/{recipient_id}")
    assert response_delete.status_code == 200
    data = response_delete.json()
    assert data["message"] == f"Account with account_id '{recipient_id}' has been deleted."


def test_get_paginated_accounts_success():
    # Mock pagination and db dependencies
    pagination_mock = MagicMock(spec=schemas.PaginationParams)
    db_mock = MagicMock()

    # Mock the pagination parameters
    pagination_mock.page = 1
    pagination_mock.page_size = 10

    # Mock the db.execute method to return some accounts
    db_mock.execute.return_value.scalars.return_value.all.return_value = [
        Account(account_id="1", name="Account 1", balance=100),
        Account(account_id="2", name="Account 2", balance=200)
    ]

    # Mock the db.execute method to return total count
    db_mock.execute.return_value.scalar.return_value = 2

    # Call the function
    result = get_paginated_accounts(pagination=pagination_mock, db=db_mock)

    # Assertions
    assert result["total_count"] == 2
    assert result["total_pages"] == 1
    assert result["current_page"] == pagination_mock.page
    assert result["page_size"] == pagination_mock.page_size
    print(result["accounts"][0].__dict__)
    assert result["accounts"][0].__dict__["account_id"] == "1"
    assert result["accounts"][0].__dict__["name"] == "Account 1"
    assert result["accounts"][0].__dict__["balance"] == 100
    assert result["accounts"][1].__dict__["account_id"] == "2"
    assert result["accounts"][1].__dict__["name"] == "Account 2"
    assert result["accounts"][1].__dict__["balance"] == 200


def test_get_paginated_accounts_no_accounts():
    # Mock pagination and db dependencies
    pagination_mock = MagicMock(spec=schemas.PaginationParams)
    db_mock = MagicMock()

    # Mock the pagination parameters
    pagination_mock.page = 1
    pagination_mock.page_size = 10

    # Mock the db.execute method to return no accounts
    db_mock.execute.return_value.scalars.return_value.all.return_value = []

    # Mock the db.execute method to return total count as 0
    db_mock.execute.return_value.scalar.return_value = 0

    # Call the function and expect HTTPException
    try:
        get_paginated_accounts(pagination=pagination_mock, db=db_mock)
    except HTTPException as exc:
        assert exc.status_code == 404
        assert exc.detail == "No accounts found for the given page"


def test_get_paginated_accounts_pagination_metadata():
    # Mock pagination and db dependencies
    pagination_mock = MagicMock(spec=schemas.PaginationParams)
    db_mock = MagicMock()

    # Mock the pagination parameters
    pagination_mock.page = 2
    pagination_mock.page_size = 10

    # Mock the db.execute method to return some accounts
    db_mock.execute.return_value.scalars.return_value.all.return_value = [
        Account(account_id=str(i), name=f"Account {i}", balance=100) for i in range(11)
    ]

    # Mock the db.execute method to return total count
    db_mock.execute.return_value.scalar.return_value = 11

    # Call the function
    result = get_paginated_accounts(pagination=pagination_mock, db=db_mock)

    # Assertions
    assert result["total_count"] == 11
    assert result["total_pages"] == 2
    assert result["current_page"] == 2
    assert result["page_size"] == 10
    assert len(result["accounts"]) == 11


def test_deposit_success(client):
    # Send request to the endpoint
    response_create = client.post(
        "/accounts",
        params={"name": "Test Account", "starting_balance": 200.0},
    )
    assert response_create.status_code == 200
    account_id = response_create.json()["account_id"]
    response = client.put(f"/accounts/{account_id}/deposit", params={"amount": 100})

    # Assertions
    assert response.status_code == 200
    print(response.json())
    assert response.json() == {"message": "Deposit successful", "balance": 300}

    # Delete the account
    response_delete = client.delete(f"/accounts/{account_id}")
    assert response_delete.status_code == 200
    data = response_delete.json()
    assert data["message"] == f"Account with account_id '{account_id}' has been deleted."


def test_export_system_state(client):
    # Mock accounts data
    accounts = [
        {"name": "Alice", "balance": 100.0},
        {"name": "Bob", "balance": 200.0},
    ]

    # Mock the db.execute method to return accounts
    # db_mock = mock_get_db()
    # db_mock.execute.return_value.scalars.return_value.all.return_value = accounts
    for i, account in enumerate(accounts):
        response_create = client.post(
            "/accounts",
            params={"name": account["name"], "starting_balance": account["balance"]},
        )
        accounts[i]["account_id"] = response_create.json()["account_id"]
    # Send request to the endpoint
    response = client.get("/save")

    # Assertions
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert response.headers["content-disposition"] == "attachment; filename=system_state.csv"

    # Validate CSV content
    csv_content = response.text
    csv_reader = csv.reader(io.StringIO(csv_content))
    header = next(csv_reader)
    assert header == ["account_id", "name", "balance"]
    rows = list(csv_reader)
    assert len(rows) == len(accounts)
    for i, row in enumerate(rows):
        print(row)
        print(accounts[i])
        assert row == [accounts[i]["account_id"], accounts[i]["name"], str(accounts[i]["balance"])]

    # Delete the account
    for account in accounts:
        response_delete = client.delete(f"/accounts/{account['account_id']}")
        assert response_delete.status_code == 200
        data = response_delete.json()
        assert data["message"] == f"Account with account_id '{account['account_id']}' has been deleted."


def test_import_system_state(client):
    # Define CSV content
    csv_content = (
        "account_id,name,balance\n"
        "d4cdc8fa-ff88-477a-b531-c4267543fff6,Alice,100\n"
        "d4cdc8fa-ff88-477a-b531-c4267543fff5,Bob,200\n"
    )

    # Mock UploadFile
    file = ("file.csv", io.BytesIO(csv_content.encode()))

    # Send request to the endpoint
    response = client.post("/load", files={"file": file})
    assert response.status_code == 200
    assert response.json() == {"message": "Import successful"}

    # Check result
    response_get = client.get(f"/accounts/d4cdc8fa-ff88-477a-b531-c4267543fff6")
    assert response_get.status_code == 200
    data = response_get.json()
    assert data["account_id"] == "d4cdc8fa-ff88-477a-b531-c4267543fff6"
    assert data["name"] == "Alice"
    assert data["balance"] == 100.0

    response_get = client.get(f"/accounts/d4cdc8fa-ff88-477a-b531-c4267543fff5")
    assert response_get.status_code == 200
    data = response_get.json()
    assert data["account_id"] == "d4cdc8fa-ff88-477a-b531-c4267543fff5"
    assert data["name"] == "Bob"
    assert data["balance"] == 200.0
