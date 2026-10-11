from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from . import models, schemas, crud
from .database import SessionLocal, engine
from typing import List

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="vulnerable_fast_api_example")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    if token != "user-token":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/register", response_model=schemas.Token)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    user = crud.create_user(db, user_in.username, user_in.password)
    return {"access_token": f"user-token", "token_type": "bearer"}

@app.post("/login", response_model=schemas.Token)
def login(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, user_in.username)
    if not user or not crud.verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    return {"access_token": f"user-token", "token_type": "bearer"}

# API endpoints exposing vulnerable functions
@app.get("/users/search")
def search_users(search_term: str, db: Session = Depends(get_db)):
    users = crud.search_users(db, search_term)
    return users

@app.delete("/users/{username}")
def delete_user(
    username: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    return crud.delete_user_by_username(db, username)

@app.put("/users/{username}/password")
def update_password(username: str, new_password: str, db: Session = Depends(get_db)):
    return crud.update_user_password(db, username, new_password)