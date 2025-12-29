from typing import TypeVar, Generic
from pydantic import BaseModel

T = TypeVar('T')


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = 1
    page_size: int = 10
    
    @property
    def skip(self) -> int:
        """Calculate number of records to skip"""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Get page size limit"""
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response"""
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    @classmethod
    def create(cls, items: list[T], total: int, page: int, page_size: int):
        """Create a paginated response"""
        total_pages = (total + page_size - 1) // page_size
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
