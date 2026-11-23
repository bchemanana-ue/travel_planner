from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Float,
    Text,
    Numeric
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    max_user_id = Column(String, unique=True, nullable=False)
    display_name = Column(String, nullable=True)

    role = Column(
        String,
        nullable=False,
        default="user",
        server_default="user"
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    trips = relationship("Trip", back_populates="user")


class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    days = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates="trips")
    places = relationship("TripPlace", back_populates="trip")


class Place(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=False)
    region = Column(String, nullable=False)

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    average_price = Column(Numeric(12, 2), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    trips = relationship("TripPlace", back_populates="place")


class TripPlace(Base):
    __tablename__ = "trip_places"

    id = Column(Integer, primary_key=True, index=True)

    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    place_id = Column(Integer, ForeignKey("places.id"), nullable=False)

    trip = relationship("Trip", back_populates="places")
    place = relationship("Place", back_populates="trips")


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)

    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False, unique=True)

    transport = Column(Numeric(12, 2), default=0)
    accommodation = Column(Numeric(12, 2), default=0)
    food = Column(Numeric(12, 2), default=0)
    activities = Column(Numeric(12, 2), default=0)

    reserve = Column(Numeric(12, 2), default=0)
    total = Column(Numeric(12, 2), default=0)

    trip = relationship("Trip")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=True)

    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    trip = relationship("Trip")