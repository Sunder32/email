from fastapi import Query


class PaginationParams:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        size: int = Query(50, ge=1, le=200, description="Items per page"),
    ):
        self.page = page
        self.size = size
        self.offset = (page - 1) * size
