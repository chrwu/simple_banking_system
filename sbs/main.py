from fastapi import FastAPI, HTTPException, Depends, Query, UploadFile, File, Response
from fastapi.responses import StreamingResponse
from typing import List
from sqlalchemy import func
from sqlalchemy.future import select
import uuid
import csv
import io
import os

from sbs.db import get_db, engine
from sbs.models import Account as AccountModel, Base
from sbs import schemas


app = FastAPI(
    title="Simple Banking System",
    description="A simple banking system with FastAPI, PostgreSQL, and Docker",
    version="1.0.0",
)


# Startup event to initialize the database
import time
from sqlalchemy.exc import OperationalError


# Startup event to initialize the database with retries
@app.on_event("startup")
def on_startup():
    retry_attempts = 5  # Number of retries
    retry_delay = 2  # Delay in seconds between retries

    for attempt in range(retry_attempts):
        try:
            with engine.begin() as conn:
                Base.metadata.create_all(conn)  # Initialize the database
            break  # If successful, exit the retry loop
        except OperationalError:
            if attempt < retry_attempts - 1:
                time.sleep(retry_delay)  # Wait before retrying
            else:
                raise  # If retries are exhausted, raise the exception


@app.get("/accounts", summary="Fetch records with pagination")
def get_paginated_accounts(
        pagination: schemas.PaginationParams = Depends(),
        db=Depends(get_db),
):
    page = pagination.page
    page_size = pagination.page_size
    offset = (page - 1) * page_size  # Calculate offset

    # Query with limit and offset for pagination
    stmt = select(AccountModel).limit(page_size).offset(offset)
    result = db.execute(stmt)
    accounts = result.scalars().all()  # Get all results for the specified page

    # Get the total count of records for pagination metadata
    total_count_stmt = select(func.count(AccountModel.account_id))
    total_count_result = db.execute(total_count_stmt)
    total_count = total_count_result.scalar()  # Retrieve the count

    # Calculate the total number of pages
    total_pages = (total_count + page_size - 1) // page_size  # Ceiling division

    if not accounts:
        raise HTTPException(status_code=404, detail="No accounts found for the given page")

    return {
        "total_count": total_count,
        "total_pages": total_pages,
        "current_page": page,
        "page_size": page_size,
        "accounts": accounts,
    }


# Endpoint to create a new bank account
@app.post("/accounts")
def create_account(
        name: str,
        starting_balance: float,
        db=Depends(get_db)
):
    account_id = str(uuid.uuid4())
    new_account = AccountModel(
        account_id=account_id,
        name=name,
        balance=starting_balance,
    )

    db.add(new_account)
    db.commit()
    db.refresh(new_account)

    return {
        "account_id": new_account.account_id,
        "name": new_account.name,
        "balance": new_account.balance
    }


# Endpoint to get account details by ID
@app.get("/accounts/{account_id}")
def get_account(
        account_id: str, db=Depends(get_db)
):
    stmt = select(AccountModel).where(AccountModel.account_id == account_id)
    result = db.execute(stmt)
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Confirm 'account_id' is valid
    if 'account_id' not in account.__dict__:
        raise KeyError("The returned object doesn't contain 'account_id'")

    return {
        "account_id": account.account_id,
        "name": account.name,
        "balance": account.balance
    }


# **Endpoint to update account data by account_id**
@app.put("/accounts/{account_id}", summary="Update account data by account_id")
def update_account(
        account_id: str,
        name: str,
        balance: float,
        db=Depends(get_db),
):
    # Find the existing account
    stmt = select(AccountModel).where(AccountModel.account_id == account_id)
    result = db.execute(stmt)  # Await the query
    account = result.scalar_one_or_none()  # Retrieve the existing account

    if not account:
        # If account doesn't exist, raise an error
        raise HTTPException(status_code=404, detail="Account not found")

    # Update the account's data
    account.name = name
    account.balance = balance

    # Commit the changes to the database
    db.commit()  # Commit the transaction
    db.refresh(account)  # Refresh the account to reflect changes

    return {
        "message": f"Account with account_id '{account_id}' has been updated.",
        "account": {
            "account_id": account.account_id,
            "name": account.name,
            "balance": account.balance,
        },
    }


@app.delete("/accounts/{account_id}", summary="Delete an account by account_id")
def delete_account(
        account_id: str, db=Depends(get_db)
):
    # Find the account by account_id
    stmt = select(AccountModel).where(AccountModel.account_id == account_id)
    result = db.execute(stmt)  # Await the database query
    account = result.scalar_one_or_none()  # Retrieve the account or None

    if not account:
        # If account does not exist, raise HTTP 404 error
        raise HTTPException(status_code=404, detail=f"Account with account_id '{account_id}' not found")

    # Store information about the account to be deleted
    account_info = {
        "account_id": account.account_id,
        "name": account.name,
        "balance": account.balance,
    }

    # Delete the account from the database
    db.delete(account)  # Delete the record
    db.commit()  # Commit the transaction to apply the changes

    # Return a confirmation message along with deleted account info
    return {
        "message": f"Account with account_id '{account_id}' has been deleted.",
        "deleted_account": account_info,
    }


# Endpoint to deposit money into an account
@app.put("/accounts/{account_id}/deposit")
def deposit(
        account_id: str,
        amount: float = Query(..., ge=0),
        db=Depends(get_db),
):
    stmt = select(AccountModel).where(AccountModel.account_id == account_id)
    result = db.execute(stmt)
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    account.balance += amount
    db.commit()
    db.refresh(account)

    return {"message": "Deposit successful", "balance": account.balance}


# Endpoint to withdraw money from an account
@app.put("/accounts/{account_id}/withdraw")
def withdraw(
        account_id: str,
        amount: float,
        db=Depends(get_db),
):
    stmt = select(AccountModel).where(AccountModel.account_id == account_id)
    result = db.execute(stmt)
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if account.balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    account.balance -= amount
    db.commit()
    db.refresh(account)

    return {
        "message": "Withdrawal successful",
        "balance": account.balance
    }


# Corrected endpoint to transfer money between accounts
@app.put("/accounts/{sender_id}/transfer/{recipient_id}")
def transfer(
        sender_id: str,
        recipient_id: str,
        amount: float,  # Using the correct request body schema
        db=Depends(get_db),
):
    # Validate sender and recipient accounts
    sender_stmt = select(AccountModel).where(AccountModel.account_id == sender_id)
    recipient_stmt = select(AccountModel).where(AccountModel.account_id == recipient_id)

    sender_result = db.execute(sender_stmt)  # Await the query
    recipient_result = db.execute(recipient_stmt)  # Await the query

    sender = sender_result.scalar_one_or_none()  # Get sender account
    recipient = recipient_result.scalar_one_or_none()  # Get recipient account

    if not sender:
        raise HTTPException(status_code=404, detail=f"Sender account '{sender_id}' not found")
    if not recipient:
        raise HTTPException(status_code=404, detail=f"Recipient account '{recipient_id}' not found")

    # Check if sender has sufficient balance for the transfer
    if sender.balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance for transfer")

    # Perform the transfer
    sender.balance -= amount
    recipient.balance += amount

    db.commit()  # Commit the changes to the database
    db.refresh(sender)  # Refresh sender account
    db.refresh(recipient)  # Refresh recipient account

    return {
        "message": "Transfer successful",
        "sender": {"account_id": sender.account_id, "balance": sender.balance},
        "recipient": {"account_id": recipient.account_id},
    }


# **Export System State to CSV**
@app.get("/save", summary="Export system state to CSV")
def export_system_state(db=Depends(get_db)):
    stmt = select(AccountModel)
    result = db.execute(stmt)
    accounts = result.scalars().all()  # Await to avoid coroutine issues

    # Create a CSV in memory
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["account_id", "name", "balance"])
    writer.writeheader()

    for account in accounts:
        writer.writerow({
            "account_id": account.account_id,
            "name": account.name,
            "balance": account.balance,
        })

    # Reset the buffer's position to read from it
    output.seek(0)

    # Return as a streaming response
    return StreamingResponse(
        output,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=system_state.csv"},
    )


# **Import System State from CSV**
@app.post("/load", summary="Import system state from CSV")
def import_system_state(
        file: UploadFile = File(...), db=Depends(get_db)
):
    content = file.file.read()  # Read file content synchronously
    content_str = content.decode("utf-8")  # Convert to string
    reader = csv.DictReader(io.StringIO(content_str))

    # Insert or update accounts from CSV
    with db.begin():
        for row in reader:
            if "account_id" not in row:
                raise HTTPException(status_code=400, detail="CSV missing 'account_id'")
            account_id = row["account_id"]
            name = row["name"]
            balance = float(row["balance"])

            # Find existing account or create a new one
            stmt = select(AccountModel).where(AccountModel.account_id == account_id)
            result = db.execute(stmt)
            account = result.scalar_one_or_none()

            if not account:
                # Create a new account
                new_account = AccountModel(
                    account_id=account_id,
                    name=name,
                    balance=balance,
                )
                db.add(new_account)
            else:
                # Update existing account
                account.name = name
                account.balance = balance

    db.commit()  # Commit changes
    return {"message": "Import successful"}
