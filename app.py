from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

# Importez votre modèle User si vous utilisez une base de données
# from .database import User, SessionLocal

app = FastAPI()

# Clé secrète pour les JWT (gardez-la en sécurité !)
SECRET_KEY = "YOUR_SECRET_KEY"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Durée de validité du token

# Configuration du hachage de mot de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 pour la connexion
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Modèles Pydantic pour la validation des données
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str

class UserCreate(BaseModel):
    username: str
    password: str

# Fonction pour créer un utilisateur (à adapter à votre base de données)
# def create_user(db: Session, user: UserCreate):
#     hashed_password = pwd_context.hash(user.password)
#     db_user = User(username=user.username, hashed_password=hashed_password)
#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)
#     return db_user

# Fonction pour récupérer un utilisateur par son nom d'utilisateur
# def get_user(db: Session, username: str):
#     return db.query(User).filter(User.username == username).first()

# Fonction pour vérifier le mot de passe
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Fonction pour créer un token JWT
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode["exp"] = expire
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Route pour la création d'un utilisateur
# @app.post("/users/", status_code=status.HTTP_201_CREATED)
# def create_user_route(user: UserCreate, db: Session = Depends(SessionLocal)):
#     db_user = get_user(db, username=user.username)
#     if db_user:
#         raise HTTPException(status_code=400, detail="Username already registered")
#     return create_user(db, user)

# Route pour la connexion et l'obtention du token
@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # db = SessionLocal()  # Si vous utilisez une base de données
    # user = get_user(db, username=form_data.username)
    # if not user or not verify_password(form_data.password, user.hashed_password):
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Incorrect username or password",
    #         headers={"WWW-Authenticate": "Bearer"},
    #     )
    # access_token = create_access_token(data={"sub": user.username})  # Utilisez le nom d'utilisateur comme sujet du token
    # return {"access_token": access_token, "token_type": "bearer"}

    # Exemple sans base de données (à des fins de démonstration)
    if form_data.username != "testuser" or form_data.password != "testpassword":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

# Route protégée (exemple)
@app.get("/items/")
async def read_items(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        token_data = TokenData(username=username)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"items": [{"name": "Foo"}, {"name": "Bar"}]}