from pydantic import BaseModel


class CatalogRes(BaseModel):
    id: str
    title: str
    description: str
    status: str = "planned"
    position: int
