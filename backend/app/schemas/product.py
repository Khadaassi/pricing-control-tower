from pydantic import BaseModel, ConfigDict


class ProductFamilyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: str | None
    brand: str | None
    model: str | None
    active: bool
    family: ProductFamilyRead
