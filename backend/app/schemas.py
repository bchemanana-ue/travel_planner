from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


class TripCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    destination: str = Field(min_length=1, max_length=200)
    days: int = Field(ge=1, le=3)


class TripResponse(BaseModel):
    id: int
    title: str
    destination: str
    days: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PlaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    category: str = Field(min_length=1, max_length=100)
    region: str = Field(min_length=1, max_length=200)

    latitude: float | None = None
    longitude: float | None = None

    average_price: float | None = Field(
        default=None,
        ge=0
    )


class TripPlaceCreate(BaseModel):
    trip_id: int = Field(gt=0)
    place_id: int = Field(gt=0)


class BudgetCreate(BaseModel):
    transport: float = Field(default=0, ge=0)
    accommodation: float = Field(default=0, ge=0)
    food: float = Field(default=0, ge=0)
    activities: float = Field(default=0, ge=0)


class ChatMessageCreate(BaseModel):
    trip_id: int | None = None
    content: str = Field(min_length=1, max_length=5000)


# Бюджет, полученный от AI
class AIPlanBudget(BaseModel):
    transport: float = Field(default=0, ge=0)
    accommodation: float = Field(default=0, ge=0)
    food: float = Field(default=0, ge=0)
    activities: float = Field(default=0, ge=0)


# Готовый план путешествия от AI
class AITripPlanCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    destination: str = Field(min_length=1, max_length=200)
    days: int = Field(ge=1, le=3)

    place_ids: list[int] = Field(
        default_factory=list
    )

    budget: AIPlanBudget | None = None