from sqlalchemy.orm import Session
from passlib.context import CryptContext
import models, schemas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Otel CRUD
def get_hotels(db: Session):
    return db.query(models.Hotel).all()

def create_hotel(db: Session, hotel: schemas.HotelCreate):
    db_hotel = models.Hotel(**hotel.dict())
    db.add(db_hotel)
    db.commit()
    db.refresh(db_hotel)
    return db_hotel

def delete_hotel(db: Session, hotel_id: int):
    hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_id).first()
    if hotel is None:
        return {"message": "Hotel not found"}
    db.delete(hotel)
    db.commit()
    return {"message": f"Hotel {hotel_id} deleted"}

def update_hotel(db: Session, hotel_id: int, hotel_data: schemas.HotelCreate):
    hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_id).first()
    if hotel:
        hotel.name = hotel_data.name
        hotel.city = hotel_data.city
        hotel.description = hotel_data.description
        hotel.price = hotel_data.price
        hotel.is_near_sea = hotel_data.is_near_sea
        hotel.has_parking = hotel_data.has_parking
        db.commit()
        db.refresh(hotel)
        return hotel
    return None

# Kullanıcı CRUD & Auth
def get_password_hash(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate, is_admin: bool = False):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        hashed_password=hashed_password,
        is_admin=is_admin  
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def get_hotels_filtered(db: Session, city: str = None, is_near_sea: bool = None, has_parking: bool = None, max_price: float = None):
    query = db.query(models.Hotel)

    if city:
        query = query.filter(models.Hotel.city.ilike(f"%{city}%"))
    if is_near_sea is not None:
        query = query.filter(models.Hotel.is_near_sea == is_near_sea)
    if has_parking is not None:
        query = query.filter(models.Hotel.has_parking == has_parking)
    if max_price is not None:
        query = query.filter(models.Hotel.price <= max_price)

    return query.all()

def get_hotel_by_id(db: Session, hotel_id: int):
    return db.query(models.Hotel).filter(models.Hotel.id == hotel_id).first()

# Review CRUD
def create_review(db: Session, review: schemas.ReviewCreate, user_id: int):
    db_review = models.Review(
        hotel_id=review.hotel_id,
        user_id=user_id,
        rating=review.rating,
        comment=review.comment
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review

def get_reviews_by_hotel(db: Session, hotel_id: int):
    return db.query(models.Review).filter(models.Review.hotel_id == hotel_id).all()


def get_average_rating(db: Session, hotel_id: int):
    reviews = db.query(models.Review).filter(models.Review.hotel_id == hotel_id).all()
    if not reviews:
        return 0
    total = sum(r.rating for r in reviews)
    return round(total / len(reviews), 1)
