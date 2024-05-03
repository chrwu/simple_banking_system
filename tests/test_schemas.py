import pytest
from pydantic import ValidationError
from sbs.schemas import PaginationParams


def test_pagination_params_default_values():
    """
    Test default values for PaginationParams.
    """
    pagination_params = PaginationParams()
    assert pagination_params.page == 1
    assert pagination_params.page_size == 10


def test_pagination_params_valid_values():
    """
    Test valid values for PaginationParams.
    """
    pagination_params = PaginationParams(page=2, page_size=20)
    assert pagination_params.page == 2
    assert pagination_params.page_size == 20


def test_pagination_params_invalid_page():
    """
    Test invalid page value for PaginationParams.
    """
    with pytest.raises(ValidationError):
        PaginationParams(page=0, page_size=10)


def test_pagination_params_invalid_page_size():
    """
    Test invalid page_size value for PaginationParams.
    """
    with pytest.raises(ValidationError):
        PaginationParams(page=1, page_size=0)


def test_pagination_params_description():
    """
    Test description field for PaginationParams.
    """
    assert PaginationParams.model_fields["page"].description == "Page number (starting from 1)"
    assert PaginationParams.model_fields["page_size"].description == "Number of records per page"
