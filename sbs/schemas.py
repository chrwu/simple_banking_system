from pydantic import BaseModel, Field


# Pagination parameters model
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number (starting from 1)")
    page_size: int = Field(10, ge=1, description="Number of records per page")
