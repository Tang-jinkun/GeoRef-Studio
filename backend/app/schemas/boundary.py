from pydantic import BaseModel


class BoundaryDatasetRead(BaseModel):
    id: str
    file_name: str
    size_bytes: int
