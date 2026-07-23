from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
from backend.app.core.database import get_db
from backend.app.core.security import get_password_hash, verify_password, create_access_token, decode_access_token
from backend.app.models.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="api/auth/token", auto_error=False)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    favorite_genres: Optional[str] = ""

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    role: str
    reading_streak: int
    xp_points: int
    badges: str
    favorite_genres: str
    reading_challenge_count: int
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    sub = decode_access_token(token)
    if sub is None:
        raise credentials_exception
    user = db.query(User).filter(User.email == sub).first()
    if user is None:
        raise credentials_exception
    return user

def get_optional_current_user(token: Optional[str] = Depends(oauth2_scheme_optional), db: Session = Depends(get_db)) -> Optional[User]:
    if not token:
        return None
    sub = decode_access_token(token)
    if sub is None:
        return None
    return db.query(User).filter(User.email == sub).first()


@router.post("/register", response_model=UserResponse)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user_in.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        favorite_genres=user_in.favorite_genres,
        role="user",
        badges="first_login"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update active streak log
    now = datetime.utcnow()
    delta = now - user.last_active_at
    if delta.days == 1:
        user.reading_streak += 1
    elif delta.days > 1:
        user.reading_streak = 1 # reset streak
    else:
        if user.reading_streak == 0:
            user.reading_streak = 1
            
    user.last_active_at = now
    db.commit()
    db.refresh(user)

    access_token = create_access_token(subject=user.email)
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/challenge", response_model=UserResponse)
def update_challenge(count: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.reading_challenge_count = count
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/leaderboard", response_model=List[UserResponse])
def get_leaderboard(db: Session = Depends(get_db)):
    # Fetch top 10 users ranked by XP
    users = db.query(User).order_by(User.xp_points.desc()).limit(10).all()
    return users

@router.get("/oauth/{provider}")
def oauth_login(provider: str):
    return {"message": f"Redirecting to {provider} OAuth flow... (Mocked for Next.js OAuth Integration)"}
