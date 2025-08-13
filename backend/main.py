from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import crud, schemas, models
from database import SessionLocal, engine
from datetime import timedelta, datetime
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

SECRET_KEY = "change_this_to_a_very_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: models.User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_admin_user(current_user: models.User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

@app.get("/")
async def root():
    return {"message": "Otel Rezervasyon Sistemi API"}

@app.get("/hotels", response_model=list[schemas.HotelOut])
def read_hotels(
    city: Optional[str] = None,
    check_in: Optional[str] = None,
    check_out: Optional[str] = None,
    is_near_sea: Optional[bool] = None,
    has_parking: Optional[bool] = None,
    max_price: Optional[float] = None,
    db: Session = Depends(get_db)
):
    return crud.get_hotels_filtered(db, city, is_near_sea, has_parking, max_price)

@app.post("/hotels", response_model=schemas.HotelOut)
def add_hotel(
    hotel: schemas.HotelCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    return crud.create_hotel(db, hotel)

@app.delete("/hotels/{hotel_id}")
def delete_hotel(
    hotel_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    return crud.delete_hotel(db, hotel_id)

@app.put("/hotels/{hotel_id}", response_model=schemas.HotelOut)
def update_hotel(
    hotel_id: int,
    hotel: schemas.HotelCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    updated = crud.update_hotel(db, hotel_id, hotel)
    if updated:
        return updated
    raise HTTPException(status_code=404, detail="Hotel not found")

@app.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    is_first_user = db.query(models.User).count() == 0
    return crud.create_user(db, user, is_admin=is_first_user)

@app.post("/token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.UserOut)
def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    return current_user

@app.get("/users", response_model=list[schemas.UserOut])
def get_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    return db.query(models.User).all()

@app.put("/users/{user_id}/toggle-admin")
def toggle_admin_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Kendi yetkinizi değiştiremezsiniz")
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    
    user.is_admin = not user.is_admin
    db.commit()
    return {"message": "Kullanıcı yetkisi güncellendi"}

@app.get("/hotels/{hotel_id}", response_model=schemas.HotelOut)
def get_hotel_by_id_endpoint(hotel_id: int, db: Session = Depends(get_db)):
    hotel = crud.get_hotel_by_id(db, hotel_id)
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    # Ortalama rating ekle
    avg_rating = crud.get_average_rating(db, hotel_id)
    hotel.average_rating = avg_rating
    return hotel


# 📌 Review endpoint'leri
@app.post("/reviews", response_model=schemas.ReviewOut)
def add_review(
    review: schemas.ReviewCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    return crud.create_review(db, review, user_id=current_user.id)

@app.get("/hotels/{hotel_id}/reviews", response_model=list[schemas.ReviewOut])
def list_reviews(hotel_id: int, db: Session = Depends(get_db)):
    return crud.get_reviews_by_hotel(db, hotel_id)


@app.delete("/reviews/{review_id}")
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this review")
    db.delete(review)
    db.commit()
    return {"message": "Review deleted"}


@app.put("/reviews/{review_id}", response_model=schemas.ReviewOut)
def update_review(
    review_id: int,
    review_data: schemas.ReviewCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this review")
    review.comment = review_data.comment
    review.rating = review_data.rating
    db.commit()
    db.refresh(review)
    return review
