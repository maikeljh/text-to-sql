import os
import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session

from models.models import User
from models.schemas import UserCreate, UserLogin
from utils.auth import hash_password, verify_password, create_access_token
from database.db import get_db


# Security scheme for Basic Auth
security = HTTPBasic()

router = APIRouter()


@router.post("/register")
def register(
    user: UserCreate,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    expected_username = os.getenv("REGISTER_USERNAME")
    expected_password = os.getenv("REGISTER_PASSWORD")

    if not (
        secrets.compare_digest(credentials.username, expected_username)
        and secrets.compare_digest(credentials.password, expected_password)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    existing_user = db.query(User).filter_by(username=user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")

    hashed_pw = hash_password(user.password)
    new_user = User(username=user.username, password=hashed_pw)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User registered successfully", "user_id": new_user.id}


@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter_by(username=user.username).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(data={"sub": db_user.username, "user_id": db_user.id})
    return {"access_token": token, "username": db_user.username, "user_id": db_user.id}
