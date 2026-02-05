from pydantic import BaseModel


class BulkDeleteRequest(BaseModel):
    ids: list[int]


class BulkDeleteResponse(BaseModel):
    deleted_count: int
    missing_ids: list[int] = []
