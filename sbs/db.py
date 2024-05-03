from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://postgres:postgres@db:5432/simple_banking_system"

# Create synchronous engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy.future import select
#
# DATABASE_URL = "postgresql+asyncpg://postgres:postgres@db:5432/simple_banking_system"
#
# # Create async engine and session
# async_engine = create_async_engine(DATABASE_URL, echo=True)
# SessionLocal = sessionmaker(
#     autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
# )
# #Async_Session = sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)
#
#
# # Dependency to get a database session
# async def get_db():
#     async with Async_Session() as db:
#         try:
#             yield db
#         except:
#             await db.close()
