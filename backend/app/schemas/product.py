from pydantic import BaseModel, ConfigDict


class ProductBase(BaseModel):
    code: str
    name: str
    description: str | None = None
    brand: str | None = None
    model: str | None = None
    active: bool = True
    product_family_id: int


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    description: str | None = None
    brand: str | None = None
    model: str | None = None
    active: bool | None = None
    product_family_id: int | None = None


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
    image_url: str | None = None
    image_alt: str | None = None
    
