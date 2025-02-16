from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from database import get_db_connection
from models import VehicleCreate, Token, TokenData, UserCreate

from auth import oauth2_scheme, create_access_token, verify_password, SECRET_KEY
from pydantic import BaseModel

router = APIRouter()

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str


@router.get("/vehicles/")
def get_vehicles():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM vehicles")
    vehicles = cursor.fetchall()
    cursor.close()
    connection.close()
    return vehicles

# Route pour visualiser les utilisateurs
@router.get("/allusers")
def get_users():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id, username, email, password, created_at FROM users")  
    users = cursor.fetchall()
    cursor.close()
    db.close()

    return {"users": users}

# Route pour créer un utilisateur
@router.post("/addusers/")
def create_user(user: UserCreate):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (user.username, user.email, user.password))
    connection.commit()
    cursor.close()
    connection.close()
    return {"message": "Utilisateur créé"}

# Route pour modifier un utilisateur
@router.put("/updateusers/{id}")
def update_user(id: int, user: UserCreate):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE users SET username=%s, email=%s, password=%s WHERE id=%s", (user.username, user.email, user.password, id))
    connection.commit()
    cursor.close()
    connection.close()
    return {"message": "Utilisateur modifié"}

# Route pour supprimer un utilisateur
@router.delete("/deleteusers/{id}")
def delete_user(id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM users WHERE id=%s", (id,))
    connection.commit()
    cursor.close()
    connection.close()
    return {"message": "Utilisateur supprimé"}

# Route pour créer un token
@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username=%s", (form_data.username,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()

    if user is None:
        raise HTTPException(status_code=400, detail="Nom d'utilisateur incorrect")
    if not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Mot de passe incorrect")

    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

# Route pour vérifier le token
@router.get("/users/me")
async def read_users_me(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token invalide")
        return {"username": username}
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide")

