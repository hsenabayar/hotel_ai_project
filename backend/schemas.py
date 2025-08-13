from pydantic import BaseModel, EmailStr
from typing import Optional, List

# Otel şemaları
class HotelCreate(BaseModel):
    name: str
    city: str
    description: Optional[str]
    price: float
    is_near_sea: bool
    has_parking: bool

class HotelOut(HotelCreate):
    id: int
    average_rating: float = 0

    class Config:
        orm_mode = True

# Kullanıcı şemaları
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone: Optional[str]

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    is_active: bool
    is_admin: bool

    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Yorum şemaları
class ReviewBase(BaseModel):
    rating: int
    comment: Optional[str] = None

class ReviewCreate(ReviewBase):
    hotel_id: int

class ReviewOut(ReviewBase):
    id: int
    user_id: int
    hotel_id: int

    class Config:
        orm_mode = True
