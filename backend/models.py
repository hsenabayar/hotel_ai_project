from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base

class Hotel(Base):
    __tablename__ = "hotels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    city = Column(String)
    description = Column(String)
    price = Column(Float)
    is_near_sea = Column(Boolean, default=False)
    has_parking = Column(Boolean, default=False)

    reviews = relationship("Review", back_populates="hotel", cascade="all, delete")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    reviews = relationship("Review", back_populates="user", cascade="all, delete")

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    rating = Column(Integer)  # 1-5
    comment = Column(Text)

    hotel = relationship("Hotel", back_populates="reviews")
    user = relationship("User", back_populates="reviews")
