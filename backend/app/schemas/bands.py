from pydantic import BaseModel, ConfigDict, Field


class BandCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    bio: str = Field(min_length=1)


class BandUpdate(BandCreate):
    pass


class BandResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    bio: str
