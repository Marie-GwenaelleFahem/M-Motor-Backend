from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from databases import Database
from database import DATABASE_URL
import asyncpg
from pydantic import BaseModel
from auth import oauth2_scheme, create_access_token, verify_password, SECRET_KEY
import jwt
from jwt import PyJWTError


database = Database(DATABASE_URL)

router = APIRouter()

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

@router.get("/vehicles/")
async def get_vehicles():
    query = "SELECT * FROM vehicles"
    vehicles = await database.fetch_all(query)
    return vehicles

@router.get("/allusers")
async def get_users():
    query = "SELECT id, username, email, password, created_at FROM users"
    users = await database.fetch_all(query)
    return {"users": users}

@router.post("/addusers/")
async def create_user(user: UserCreate):
    query = "INSERT INTO users (username, email, password) VALUES (:username, :email, :password)"
    values = {"username": user.username, "email": user.email, "password": user.password}
    await database.execute(query, values)
    return {"message": "Utilisateur créé"}

@router.put("/updateusers/{id}")
async def update_user(id: int, user: UserCreate):
    query = "UPDATE users SET username=:username, email=:email, password=:password WHERE id=:id"
    values = {"id": id, "username": user.username, "email": user.email, "password": user.password}
    await database.execute(query, values)
    return {"message": "Utilisateur modifié"}

@router.delete("/deleteusers/{id}")
async def delete_user(id: int):
    query = "DELETE FROM users WHERE id=:id"
    await database.execute(query, {"id": id})
    return {"message": "Utilisateur supprimé"}

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    query = "SELECT * FROM users WHERE username=:username"
    user = await database.fetch_one(query, {"username": form_data.username})
    
    if user is None:
        raise HTTPException(status_code=400, detail="Nom d'utilisateur incorrect")
    if not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Mot de passe incorrect")
    
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me")
async def read_users_me(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token invalide")
        return {"username": username}
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Token invalide")
