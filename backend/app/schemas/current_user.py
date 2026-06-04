from pydantic import BaseModel, ConfigDict


class CurrentUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    active: bool
    country_id: int | None = None
    store_id: int | None = None
    roles: list[str]
    permissions: list[str]