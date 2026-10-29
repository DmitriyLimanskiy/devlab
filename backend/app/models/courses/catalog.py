from pydantic import BaseModel


class ResCatalog(BaseModel):
    id: str
    title: str
    description: str
    status: str = "planned"
