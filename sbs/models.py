from sqlalchemy import Column, String, Float
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Account(Base):
    __tablename__ = 'accounts'

    account_id = Column(String, primary_key=True)
    name = Column(String)
    balance = Column(Float)

