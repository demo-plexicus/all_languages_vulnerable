from sqlalchemy.orm import Session
from sqlalchemy import text
from . import models
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user_by_username(db: Session, username: str):
    # FIXED: Use parameterized query to prevent SQL injection
    query = text("SELECT * FROM users WHERE username = :username")
    result = db.execute(query, {"username": username})
    return result.first()

def create_user(db: Session, username: str, password: str):
    hashed = pwd_context.hash(password)
    
    # FIXED: Use parameterized query to prevent SQL injection
    query = text("INSERT INTO users (username, hashed_password) VALUES (:username, :hashed)")
    db.execute(query, {"username": username, "hashed": hashed})
    db.commit()
    
    # Get the created user (also fixed)
    get_query = text("SELECT * FROM users WHERE username = :username")
    result = db.execute(get_query, {"username": username})
    return result.first()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# ADDITIONAL MORE VULNERABLE FUNCTIONS
def search_users(db: Session, search_term: str):
    # FIXED: Use parameterized query with LIKE pattern concatenation
    pattern = f"%{search_term}%"
    query = text("SELECT * FROM users WHERE username LIKE :pattern OR email LIKE :pattern")
    result = db.execute(query, {"pattern": pattern})
    return result.fetchall()

def delete_user_by_username(db: Session, username: str):
    # FIXED: Use parameterized query to prevent SQL injection
    query = text("DELETE FROM users WHERE username = :username")
    db.execute(query, {"username": username})
    db.commit()
    return {"message": "User deleted"}

def update_user_password(db: Session, username: str, new_password: str):
    # FIXED: Use parameterized query to prevent SQL injection
    hashed = pwd_context.hash(new_password)
    query = text("UPDATE users SET hashed_password = :hashed WHERE username = :username")
    db.execute(query, {"hashed": hashed, "username": username})
    db.commit()
    return {"message": "Password updated"}

