import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sbs.models import Base, Account

# Create an in-memory SQLite database engine
engine = create_engine('sqlite:///:memory:')

# Create a sessionmaker bound to the engine
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables in the database
Base.metadata.create_all(bind=engine)


@pytest.fixture
def db_session():
    """
    Fixture to provide a database session for testing.
    """
    # Create a new database session
    session = SessionLocal()

    # Begin a new transaction
    session.begin()

    # Provide the session to the test
    yield session

    # Rollback the transaction to discard any changes
    session.rollback()

    # Close the session
    session.close()


def test_account_model(db_session):
    """
    Test the Account model.
    """
    # Create a new Account instance
    account = Account(
        account_id='123',
        name='Test Account',
        balance=100.0
    )

    # Add the account to the session
    db_session.add(account)
    db_session.commit()

    # Retrieve the account from the database
    retrieved_account = db_session.query(Account).filter_by(account_id='123').first()

    # Verify that the retrieved account matches the original account
    assert retrieved_account.account_id == '123'
    assert retrieved_account.name == 'Test Account'
    assert retrieved_account.balance == 100.0
